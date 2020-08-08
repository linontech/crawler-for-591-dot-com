import logging
import logging.config
from flask import Flask
from datetime import datetime

from flask_wtf import CSRFProtect

from app.endpoints import BP as api_bp


def register_logging():
    LOG_FORMAT = '[%(threadName)s]-[%(thread)d] %(asctime)s [%(levelname)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    timestamp = datetime.now().strftime("%Y%m%d")
    formatter = logging.Formatter(datefmt=LOG_DATE_FORMAT, fmt=LOG_FORMAT)
    handler = logging.FileHandler('log/flask.' + timestamp + '.log', encoding='UTF-8')
    handler.setFormatter(formatter)
    logger_ = logging.getLogger()
    logger_.addHandler(handler)
    logger_.setLevel(logging.INFO)
    return logger_


def create_app():
    app_ = Flask(__name__, template_folder='../dist', static_folder='../dist/static')
    app_.config.from_object('app.settings.default')
    return app_


def setup_app(app_):
    app_.register_blueprint(api_bp)
    csrf = CSRFProtect()
    csrf.init_app(app_)
    app_.logger = register_logging()
