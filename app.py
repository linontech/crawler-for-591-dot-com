import traceback
from time import strftime
from flask import request

import crawler

app = crawler.create_app()

crawler.register_blueprints(app)

logger = crawler.register_logging()


@app.errorhandler(Exception)
def exceptions(e):
    """
    Logging after every Exception.
    """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                 ts,
                 request.remote_addr,
                 request.method,
                 request.scheme,
                 request.full_path,
                 tb)
    return "Internal Server Error", 500
