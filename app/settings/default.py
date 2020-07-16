import os

# Flask settings
SECRET_KEY = os.urandom(32)

# app settings
PAGE_TITLE = "five9one"

# mongo db address
MONGODB_SERVER = 'mongodb://127.0.0.1'

MONGODB_PORT = 27017

MONGODB_DATABASE = 'five9one'

MONGODB_COLLECTION = 'houses'

FIVE9ONE_CSRF_TOKEN = ''

POOL_CONNECTIONS_NUM = 500

POOL_MAXSIZE_NUM = 500

PARSE_INTERVAL_IN_SECONDS = 1800

# config for crawl
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
