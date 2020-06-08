import concurrent.futures
import time
import re
from json import JSONDecodeError

import requests
from bs4 import BeautifulSoup
from flask import current_app

from crawler import MongoDbManager
from crawler.constants import shape_dict, lesser_role_dict, sex_requirement_dict

ROOT_URL = 'https://rent.591.com.tw'
API_URL = ROOT_URL + '/home/search/rsList'
WEB_URL_FORMAT_STR = ROOT_URL + '/rent-detail-{}.html'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'connection': 'keep-alive',
    'dnt': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
}


def get_houses(payload, session, app):
    """
    thread function for crawling houses
    :param payload:
    :param session:
    :param app:
    :return:
    """
    app.logger.info('get_houses() request sending payload: {}'.format(payload))

    response = None
    inserted_ids, data = [], {}
    try:
        response = session.get(API_URL, params=payload, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()['data']
        else:
            app.logger.error('get_houses() Request fail with http status code = {}, {}'.format(response.status_code, str(payload)))
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
        houses = _reconstruct_houses(houses, session, app)
        inserted_ids = _save_to_mongo(houses, app)
        app.logger.info('{} records crawled and saved into MongoDB. {} '.format(
            len([inserted_id for inserted_id in inserted_ids if inserted_id is not None]), str(inserted_ids)))
    finally:
        return inserted_ids


def get_houses_nums(payload):
    """
    :param payload:
    :return:
    """
    current_app.logger.info('get_houses_nums() payload: {}'.format(payload))
    response, num = None, 0
    try:
        session = requests.Session()
        _set_csrf_token(session, current_app._get_current_object())
        response = session.get(API_URL, params=payload, headers=HEADERS)
        if response.status_code == 200:
            num = int(response.json()['records'].replace(',', ''))
        else:
            current_app.logger.info(
                'get_houses_nums() Request fail with http status code = {}'.format(response.status_code))
    except requests.exceptions.RequestException as e:
        current_app.logger.error('get_houses_nums() Http Error: ', e)
    except KeyError as e:
        current_app.logger.error('get_houses_nums() KeyError Cannot get data from tel[0]["data-value"]: {}'.format(
            response.text.replace('\n', '')), e)
    except JSONDecodeError as e:
        current_app.logger.error('get_houses_nums() JSONDecodeError', e)
    finally:
        return num


def _get_tel(house, session, app):
    """
    thread function to get phone number
    :param house:
    :param session:
    :param app:
    :return:
    """
    url = WEB_URL_FORMAT_STR.format(house['post_id'])
    retry = 3
    while retry > 0:
        try:
            response = session.get(url, headers=HEADERS)
            if response.status_code == 200:
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                tel = soup.find_all('span', attrs={'data-value': True})
                if len(tel) == 1:
                    # app.logger.info('_get_tel() Found tel on {}.'.format(url))
                    if retry < 3:
                        app.logger.info('_get_tel() retryed success')
                    return tel[0]['data-value'].replace('-', '')
                else:
                    app.logger.info('_get_tel() No tel found on {}.'.format(url))
            else:
                app.logger.info('_get_tel() on {} Request fail with http status code = {}'.format(
                    url, response.status_code))
                retry -= 1
                continue
        except requests.exceptions.ConnectionError as e:
            app.logger.error('_get_tel() on {} ConnectionError'.format(url, e))
            app.logger.error('_get_tel() retrying')
            retry -= 1
            if retry < 0:
                app.logger.error('_get_tel() retryed 3 times still failed.')
        except requests.exceptions.RequestException as e:
            app.logger.error('_get_tel() on {}, RequestException: {}'.format(url, e))
        except KeyError as e:
            app.logger.error('_get_tel() on {}, KeyError Cannot get data from tel[0]["data-value"]: {}'.format(
                url, response.text.replace('\n', '')), e)
        except JSONDecodeError as e:
            app.logger.error('_get_tel() on {}, JSONDecodeError {}'.format(url, e))
    return ''


def _parse_sex_condition(condition):
    """
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


def _parse_lessor_role(nick_name, linkman):
    """
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
            '_parse_lessor_title() error. {},{},{},{}'.format(nick_name, linkman, lessor_role, lessor_name))
        return lessor_role, lessor_name
    lessor_role_end = nick_name.index(linkman)
    lessor_role, lessor_name = nick_name[:lessor_role_end], nick_name[lessor_role_end:]
    lessor_role = lesser_role_dict.get(lessor_role, '-1')
    return lessor_role, lessor_name


def _reconstruct_house(house, session, app):
    """
    thread function
    house = {'name': <str>, 'url': <str>, 'price': <str>, 'area': <str>, 'kind': <str>, 'update_time': <datetime>,
    'tel': <str>}
    :param house:
    :param session:
    :param app:
    """
    new_house = {'url': '{}'.format(WEB_URL_FORMAT_STR.format(house['post_id'])), 'name': '{}-{}-{}'.format(
        house['region_name'],
        house['section_name'],
        house['fulladdress'],
    ), 'regionid': str(house['regionid'])}

    lessor_role, lessor_name = _parse_lessor_role(house['nick_name'], house['linkman'])
    new_house['linkman'] = {'name': lessor_name, 'role': lessor_role, 'sex': _get_sex(lessor_name),
                            'tel': _get_tel(house, session, app)}

    new_house['kind'] = '{}'.format(house['kind'])
    shape = shape_dict.get(str(house['shape']), '-1')
    if shape == '-1':
        app.logger.error('不明房屋型態出現 ' + str(house['shape']) + ' ... - ' + new_house['url'])
    new_house['shape'] = '{}'.format(str(house['shape']))
    new_house['sex_requirement'] = _parse_sex_condition(house['condition'])
    if new_house['sex_requirement'] == '-1':
        app.logger.error('不明租客性別要求出現 ' + str(house['condition']) + ' ... - ' + new_house['url'])

    new_house['id'] = str(house['user_id']) + '-' + str(house['id'])
    new_house['price'] = int(house['price'].replace(',', ''))  # 元
    new_house['area'] = house['area']  # 坪
    new_house['layout'] = '{}'.format(house['layout'])
    new_house['update_time'] = '{}'.format(time.ctime(house['refreshtime']))

    return new_house


def _get_sex(name):
    """
    :param name: linkman name
    :return: 0: woman, 1: man, 2: both, 3: None
    """
    isMan = re.findall('先生|帥哥|哥', name)
    isWoman = re.findall('小姐|媽媽|媽|女士|太太|太', name)
    if not isMan and isWoman:
        return '0'
    elif isMan and not isWoman:
        return '1'
    elif isMan and isWoman: # 不限
        return '2'
    else:  # unknown
        return '3'


def _reconstruct_houses(houses, session, app):
    """

    :param houses:
    :return:
    """
    app.logger.info(f'_reconstruct_houses() start, total houses: {len(houses)}')
    start = time.time()
    new_houses = []
    with concurrent.futures.ThreadPoolExecutor(thread_name_prefix='HousesWorker-', max_workers=len(houses)) as executor:
        futures = [executor.submit(_reconstruct_house, house, session, app) for house in houses]
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


def _set_csrf_token(session, app):
    """

    :param session:
    :return:
    """
    r = session.get(ROOT_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    for tag in soup.select('meta'):
        if tag.get('name', None) == 'csrf-token':
            csrf_token = tag.get('content')
            session.headers = HEADERS
            session.headers['X-CSRF-TOKEN'] = csrf_token
            # app.logger.info(f'Found csrf-token ' + csrf_token)
            break
    else:
        app.logger.info(f'No csrf-token found')


def _save_to_mongo(houses, app):
    """
    thread function for storing houses into MongoDB
    :param houses: list of house
    :return: inserted ids
    """
    manager = MongoDbManager.get_instance(app)
    res = manager.update(houses, app)

    return res
