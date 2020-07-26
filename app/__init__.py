import os
import traceback
import logging
import logging.config
from time import strftime
from flask import Flask, url_for
from flask import current_app, request
from datetime import datetime

from flask_wtf import CSRFProtect

from app.endpoints import BP as api_bp


def create_app():
    app_ = Flask(__name__, template_folder='../dist', static_folder='../dist/static')
    app_.config.from_object('app.settings.default')
    jinja_options = app_.jinja_options.copy()
    jinja_options.update(
        dict(variable_start_string='((', variable_end_string='))')
    )
    app_.jinja_options = jinja_options
    app_.register_blueprint(api_bp)
    csrf = CSRFProtect()
    csrf.init_app(app_)
    return app_


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


app = create_app()
logger = register_logging()


@app.errorhandler(Exception)
def exceptions(e):
    """
    Logging after every Exception.
    """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    current_app.logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                              ts,
                              request.remote_addr,
                              request.method,
                              request.scheme,
                              request.full_path,
                              tb)
