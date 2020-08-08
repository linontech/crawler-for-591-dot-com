import concurrent.futures
import re
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import current_app
from json import JSONDecodeError

from app.crawl.crawl_manager import CrawlManager
from app.mongodb.mongodb_manager import MongoDbManager
from app.crawl import shape_dict, sex_requirement_dict, lesser_role_dict

lock = threading.Lock()


class HouseCrawler(CrawlManager):
    __instance = None
    duplicate_count = 0
    DEFAULT_PAYLOAD = \
        {
            'is_new_list': '1',
            'type': '1',
            'kind': '0',
            'searchtype': 1
        }

    def __init__(self):
        raise SyntaxError('can not instance, please use get_instance')

    @classmethod
    def get_instance(cls):
        """
        :return: singleton
        """
        if cls.__instance is None:
            with lock:
                if cls.__instance is None:
                    cls.__instance = object.__new__(cls)
                    cls.__instance.duplicate_count = 0
        return cls.__instance

    def _create_payloads(self):
        """
        create payloads for 台北1 新北3
        :return: payloads for crawling
        """
        each_page_num = 30
        payloads = []
        for region_id in ['1', '3']:
            self.DEFAULT_PAYLOAD['regionid'] = region_id
            total_rows = self._get_houses_nums(self.DEFAULT_PAYLOAD)
            current_app.logger.info(
                'Found {} houses for crawling'.format(total_rows))
            for i in range(each_page_num, total_rows + 1, each_page_num):
                payload = self.DEFAULT_PAYLOAD.copy()
                payload['firstRow'] = i
                payload['totalRows'] = total_rows
                payloads.append(payload)

        return payloads

    def job(self, payload, session, app):
        self.duplicate_count = 0
        return self._get_houses(payload, session, app)

    def call_back_function(self, future, session):
        tmp_dup_count, inserted_ids = 0, []
        try:
            houses = future.result()
            houses = self._reconstruct_houses(houses, session, current_app._get_current_object())
            inserted_ids = self._save_to_mongo(houses, current_app._get_current_object())
            tmp_dup_count = len(
                [inserted_id for inserted_id in inserted_ids if inserted_id.startswith('duplicate')])
        except Exception as e:
            current_app.logger.error('CrawlManager run() error: ', e)

        self.duplicate_count += tmp_dup_count
        current_app.logger.info(
            '{} records crawled and saved into MongoDB. {} '.format(
                tmp_dup_count, str(inserted_ids)))

    def _get_houses_nums(self, payload):
        """
        :param payload:
        :return:
        """
        current_app.logger.info('get_houses_nums() payload: {}'.format(payload))
        response, num = None, 0
        try:
            session = requests.Session()
            self._set_csrf_token(session)
            response = session.get(
                current_app.config.get('API_URL'),
                params=payload,
                headers=current_app.config.get('HEADERS'))
            if response.status_code == 200:
                num = int(response.json()['records'].replace(',', ''))
            else:
                current_app.logger.info(
                    'get_houses_nums() Request fail with http status code = {}'.format(response.status_code))
        except requests.exceptions.RequestException as e:
            current_app.logger.error('get_houses_nums() Http Error: ', e)
        except KeyError as e:
            current_app.logger.error(
                'get_houses_nums() KeyError Cannot get data from tel[0]["data-value"]: {}'.format(
                    response.text.replace('\n', '')), e)
        except JSONDecodeError as e:
            current_app.logger.error('get_houses_nums() JSONDecodeError', e)
        finally:
            return num

    def _get_houses(self, payload, session, app):
        """
        thread function for crawling houses
        :param payload:
        :param session:
        :param app:
        :return:
        """
        app.logger.info('get_houses() request sending payload: {}'.format(payload))

        response = None
        houses, data = [], {}
        try:
            response = session.get(app.config.get('API_URL'), params=payload, headers=app.config.get('HEADERS'))
            if response.status_code == 200:
                data = response.json()['data']
            else:
                app.logger.error('get_houses() Request fail with http status code = {}, {}'.format(
                        response.status_code, str(payload)))
        except requests.exceptions.RequestException as e:
            app.logger.error('get_houses() Http Error: ', e)
        except KeyError as e:
            app.logger.error('get_houses() KeyError Cannot get data from response.json["data"]: {}'.format(
                response.text.replace('\n', '')), e)
        except JSONDecodeError as e:
            app.logger.error('get_houses() JSONDecodeError', e)
        except Exception as e:
            app.logger.error('get_houses() ', e)
        else:
            houses = data.get('data', [])
        finally:
            return houses

    def _get_tel(self, house, session, app):
        """
        thread function to get phone number
        :param house:
        :param session:
        :param app:
        :return:
        """
        url = app.config.get('WEB_URL_FORMAT_STR').format(house['post_id'])
        retry, tel = 3, ''
        while retry > 0:
            try:
                response = session.get(url, headers=app.config.get('HEADERS'))
                if response.status_code == 200:
                    html = response.content
                    soup = BeautifulSoup(html, 'html.parser')
                    val = soup.find_all('span', attrs={'data-value': True})
                    if len(val) == 1:
                        tel = val[0]['data-value'].replace('-', '')
                    else:
                        app.logger.info('_get_tel() No tel found on {}.'.format(url))
                    break
                else:
                    app.logger.info(
                        '_get_tel() on {} Request fail with http status code = {}, retrying ... left {}'.format(
                            url, response.status_code, retry))
                    retry -= 1
                    continue
            except requests.exceptions.ConnectionError as e:
                app.logger.error(
                    '_get_tel() on {} , retrying ... left {}, ConnectionError {}'.format(url, retry, e))
                retry -= 1
            except requests.exceptions.RequestException as e:
                app.logger.error(
                    '_get_tel() on {}, RequestException: {}'.format(url, e))
            except KeyError as e:
                app.logger.error(
                    '_get_tel() on {}, KeyError Cannot get data from tel[0]["data-value"]: {}'.format(
                        url, response.text.replace('\n', '')), e)
            except JSONDecodeError as e:
                app.logger.error(
                    '_get_tel() on {}, JSONDecodeError {}'.format(url, e))
            finally:
                if 0 < retry < 3 and tel != '':
                    app.logger.info('_get_tel() retried success')
                if retry == 0:
                    app.logger.error('_get_tel() retried 3 times still failed.')

        return tel

    def _reconstruct_houses(self, houses, session, app):
        """
        thread function
        :param houses:
        :return:
        """
        app.logger.info(
            f'_reconstruct_houses() start, total houses: {len(houses)}')
        start = time.time()
        new_houses = []
        with concurrent.futures.ThreadPoolExecutor(thread_name_prefix='HousesWorker',
                                                   max_workers=len(houses)) as executor:
            futures = [
                executor.submit(self._reconstruct_house, house, session, app) for house in houses
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    new_house = future.result()
                except Exception as e:
                    app.logger.error('_reconstruct_houses()  error: ', e)
                else:
                    new_houses.append(new_house)
        end = time.time()
        app.logger.info(f'_reconstruct_houses() done spent: {end - start} seconds')

        return new_houses

    def _reconstruct_house(self, house, session, app):
        """
        thread function
        house = {'name': <str>, 'url': <str>, 'price': <str>, 'area': <str>, 'kind': <str>, 'update_time': <datetime>,
        'tel': <str>}
        :param house:
        :param session:
        :param app:
        """
        new_house = dict(
            url='{}'.format(
                app.config.get('WEB_URL_FORMAT_STR').format(
                    house['post_id'])),
            name='{}-{}-{}'.format(
                house['region_name'],
                house['section_name'],
                house['fulladdress'],
            ),
            regionid=str(
                house['regionid']))

        lessor_role, lessor_name = self._parse_lessor_role(
            house['nick_name'], house['linkman'])
        new_house['linkman'] = {
            'name': lessor_name,
            'role': lessor_role,
            'sex': self._get_sex(lessor_name),
            'tel': self._get_tel(
                house,
                session,
                app)}

        new_house['kind'] = '{}'.format(house['kind'])
        shape = shape_dict.get(str(house['shape']), '-1')
        if shape == '-1':
            app.logger.error('不明房屋型態出現 ' +
                             str(house['shape']) +
                             ' ... - ' +
                             new_house['url'])
        new_house['shape'] = '{}'.format(str(house['shape']))
        new_house['sex_requirement'] = self._parse_sex_condition(
            house['condition'])
        if new_house['sex_requirement'] == '-1':
            app.logger.error('不明租客性別要求出現 ' +
                             str(house['condition']) +
                             ' ... - ' +
                             new_house['url'])

        new_house['id'] = str(house['user_id']) + '-' + str(house['id'])
        new_house['price'] = int(house['price'].replace(',', ''))  # 元
        new_house['area'] = house['area']  # 坪
        new_house['layout'] = '{}'.format(house['layout'])
        new_house['update_time'] = '{}'.format(
            time.ctime(house['refreshtime']))

        return new_house

    def _get_sex(self, name):
        """
        thread function
        :param name: linkman name
        :return: 0: woman, 1: man, 2: both, 3: None
        """
        isMan = re.findall('先生|帥哥|哥', name)
        isWoman = re.findall('小姐|媽媽|媽|女士|太太|太', name)
        if not isMan and isWoman:
            return '0'
        elif isMan and not isWoman:
            return '1'
        elif isMan and isWoman:  # 不限
            return '2'
        else:  # unknown
            return '3'

    def _parse_sex_condition(self, condition):
        """
        thread function
        :param condition: list of condition
        :return: 映射後的字符串
        """
        if 'all_sex' in condition:
            return sex_requirement_dict['all_sex']
        if 'boy' in condition:
            return sex_requirement_dict['boy']
        if 'girl' in condition:
            return sex_requirement_dict['girl']

        return sex_requirement_dict['all_sex']

    def _parse_lessor_role(self, nick_name, linkman):
        """
        thread function
        注意：梁先生免費服務. pattern too complex
        :param nick_name: eg. 中介 勸業房屋, 屋主 林先生
        :param linkman: eg. 林先生, 路 小姐
        :return: lessor_role, lessor_name=lessor
        """
        lessor_role, lessor_name = '-1', '-1'
        nick_name = nick_name.replace(' ', '')
        linkman = linkman.replace(' ', '')
        if linkman not in nick_name:
            current_app.logger.error(
                '_parse_lessor_title() error. {},{},{},{}'.format(
                    nick_name, linkman, lessor_role, lessor_name))
            return lessor_role, lessor_name
        lessor_role_end = nick_name.index(linkman)
        lessor_role, lessor_name = nick_name[:
                                             lessor_role_end], nick_name[lessor_role_end:]
        lessor_role = lesser_role_dict.get(lessor_role, '-1')
        return lessor_role, lessor_name

    def _save_to_mongo(self, houses, app):
        """
        thread function for storing houses into MongoDB
        :param houses: list of house
        :return: inserted ids
        """
        manager = MongoDbManager.get_instance()
        if manager is not None:
            res = manager.update(houses)
            return res
        else:
            return []
