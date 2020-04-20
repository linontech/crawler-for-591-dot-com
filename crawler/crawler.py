import concurrent.futures
import time

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


def get_houses(payload):
    """
    main function for crawling houses
    :param payload:
    :return:
    """
    current_app.logger.info('get_houses() request sending payload: {}'.format(payload))
    session = requests.Session()
    _set_csrf_token(session)

    response = session.get(API_URL, params=payload, headers=HEADERS)
    try:
        data = response.json()['data']
    except KeyError:
        current_app.logger.error('response.json()["data"]: {}'.format(response.json()["data"]))
        current_app.logger.error('Cannot get data from response.json["data"]')
    except Exception:
        current_app.logger.error('response: {}'.format(response.text))
        raise
    else:
        houses = data.get('data', [])
        houses = _reconstruct_houses(houses)
        inserted_ids = _save_to_mongo(houses)
        current_app.logger.info(str(inserted_ids))
        return inserted_ids


def _get_tel(house):
    """

    :param house:
    :return:
    """
    target = WEB_URL_FORMAT_STR.format(house['post_id'])
    response = requests.get(target, headers=HEADERS)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    tel = soup.find_all('span', attrs={'data-value': True})
    if tel:
        return tel[0]['data-value'].replace('-', '')
    return ''


def get_houses_nums(payload):
    """

    :param payload:
    :return:
    """
    current_app.logger.info('get_houses_nums() payload: {}'.format(payload))
    session = requests.Session()
    _set_csrf_token(session)
    response = session.get(API_URL, params=payload, headers=HEADERS)
    num = int(response.json()['records'].replace(',', ''))

    return num


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
    :param nick_name: 中介 勸業房屋, 屋主 林先生
    :param linkman: 林先生, 路 小姐
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
    # current_app.logger.info('_parse_lessor_title() info. {},{},{},{}'.format(nick_name, linkman, lessor_role, lessor_name))
    return lessor_role, lessor_name


def _reconstruct_house(house):
    """
    house = {'name': <str>, 'url': <str>, 'price': <str>, 'area': <str>, 'kind': <str>, 'update_time': <datetime>,
    'tel': <str>}
    """
    new_house = {}
    new_house['url'] = '{}'.format(WEB_URL_FORMAT_STR.format(house['post_id']))
    new_house['name'] = '{}-{}-{}'.format(
        house['region_name'],
        house['section_name'],
        house['fulladdress'],
    )
    new_house['regionid'] = str(house['regionid'])

    lessor_role, lessor_name = _parse_lessor_role(house['nick_name'], house['linkman'])
    new_house['linkman_role'] = lessor_role
    new_house['linkman'] = lessor_name

    new_house['tel'] = _get_tel(house)
    new_house['kind'] = '{}'.format(house['kind'])
    shape = shape_dict.get(str(house['shape']), '-1')
    if shape == '-1':
        current_app.logger.error('不明房屋型態出現 ' + str(house['shape']) + ' ... - ' + new_house['url'])
    new_house['shape'] = '{}'.format(str(house['shape']))
    new_house['sex_requirement'] = _parse_sex_condition(house['condition'])
    if new_house['sex_requirement'] == '-1':
        current_app.logger.error('不明租客性別要求出現 ' + str(house['condition']) + ' ... - ' + new_house['url'])

    new_house['id'] = str(house['user_id']) + '-' + str(house['id'])
    new_house['price'] = '{} {}'.format(house['price'], house['unit'])
    new_house['area'] = '{} 坪'.format(house['area'])
    new_house['layout'] = '{}'.format(house['layout'])
    new_house['update_time'] = '{}'.format(time.ctime(house['refreshtime']))

    return new_house


def _reconstruct_houses(houses):
    """

    :param houses:
    :return:
    """
    current_app.logger.info(f'_reconstruct_houses() start, total houses: {len(houses)}')
    start = time.time()
    new_houses = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(houses)) as executor:
        futures = [executor.submit(_reconstruct_house, house) for house in houses]
        for future in concurrent.futures.as_completed(futures):
            try:
                new_house = future.result()
            except Exception as e:
                current_app.logger.error('parse houses error: ', e)
            else:
                new_houses.append(new_house)
    end = time.time()
    current_app.logger.info(f'_reconstruct_houses() spent: {end - start} seconds')

    return new_houses


def _set_csrf_token(session):
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
            break
    else:
        current_app.logger.info(f'No csrf-token found')
        pass


def _save_to_mongo(houses):
    """
    input: list of data
    schema: ?
    :param houses:
    :return:
    """
    client = MongoDbManager.get_instance(current_app)
    client.check_target_db()
    client.check_target_collection()

    res = client.update(houses)

    current_app.logger.info('save_to_mongo() data save success. ')
    return res
