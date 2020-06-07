import logging
import logging.config
from datetime import datetime
from flask import Flask
from crawler.MongoDbManager import MongoDbManager


def create_app():
    app = Flask(__name__)
    app.config.from_object('crawler.settings.default')

    return app


def register_blueprints(app):
    from crawler.endpoints import BP as root

    app.register_blueprint(root)


def register_logging():
    LOG_FORMAT = '[%(threadName)s]-[%(thread)d] %(asctime)s [%(levelname)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    timestamp = datetime.now().strftime("%Y%m%d")
    formatter = logging.Formatter(datefmt=LOG_DATE_FORMAT, fmt=LOG_FORMAT)
    handler = logging.FileHandler('log/flask.' + timestamp + '.log', encoding='UTF-8')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
