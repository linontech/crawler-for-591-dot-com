PARSE_INTERVAL_IN_SECONDSROOT_URL = "https://rent.591.com.tw"
API_URL = "https://rent.591.com.tw/home/search/rsList"

HEADERS = {
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'accept-encoding': "gzip, deflate, br",
    'accept-language': "en-US,en;q=0.9",
    'connection': "keep-alive",
    'dnt': "1",
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36",
}

WEB_URL_FORMAT_STR = "https://rent.591.com.tw/rent-detail-{}.html"

PARSE_INTERVAL_IN_SECONDS = 1800

kind_dict = {
    '0': '不限',
    '1': '整層住家',
    '2': '獨立套房',
    '3': '分租套房',
    '4': '雅房',
    '8': '車位',
    '24': '其他',
}

regionid_dict = {
    '1', '台北市',
    '3', '新北市',
}

shape_dict = {
    '0': '不限',
    '1': '公寓',
    '2': '電梯大樓',
    '3': '透天厝',
    '4': '別墅',
    '5': '華廈',
    '6': '住宅大樓',
    '-1': 'unknown',
}

lesser_role_dict = {
    '屋主': '0',
    '代理人': '1',
    '仲介': '2',
    'unknown': '-1',
}

sex_requirement_dict = {
    'all_sex': '0',
    'boy': '1',
    'girl': '2',
    'unknown': '-1'
}

sex_dict = {
    '不限': '0',
    '男': '1',
    '女': '2',
}

lessor_sex_dict = {
    '不限': '0',
    '先生': '1',
    '小姐': '2',
    '女士': '2',
    '太太': '2',
    '媽媽': '2',
    'unknown': '-1',
}
