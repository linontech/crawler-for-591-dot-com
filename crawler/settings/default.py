import os

# Flask settings
SECRET_KEY = os.urandom(32)

# crawler settings
PAGE_TITLE = "five9one"

# mongo db address
MONGODB_SERVER = 'mongodb://127.0.0.1'

MONGODB_PORT = 27017

MONGODB_DATABASE = 'five9one'

MONGODB_COLLECTION = 'houses'

FIVE9ONE_CSRF_TOKEN = ''

POOL_CONNECTIONS_NUM = 100

POOL_MAXSIZE_NUM = 100
