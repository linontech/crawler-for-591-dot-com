import traceback
from time import strftime

from flask import current_app, request

from app import create_app, setup_app

app = create_app()
setup_app(app)


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

