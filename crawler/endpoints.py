from flask import (
    Blueprint,
    render_template,
    current_app,
    request,
    make_response)
from crawler import MongoDbManager
from crawler.CrawlManager import CrawlManager
from crawler.forms import QueryForm

BP = Blueprint('root', __name__)


@BP.route("/", methods=["GET"])
def index():
    form = QueryForm()
    return render_template(
        'index.html',
        title=current_app.config.get('PAGE_TITLE'),
        form=form,
    )


@BP.route("/start", methods=["POST"])
def start_crawl():
    crawl_manager = CrawlManager.get_instance()
    if not crawl_manager.is_running():
        payloads = crawl_manager.create_payloads()
        message = crawl_manager.run(payloads)
        data = {'message': message, 'code': 'SUCCESS'}
    else:
        data = {'message': 'crawler exists...', 'code': 'SUCCESS'}
    return make_response(data, 201)


@BP.route("/stop", methods=["POST"])
def stop_crawl():
    crawl_manager = CrawlManager.get_instance()
    if crawl_manager.stop():
        return make_response({'message': 'stopped.'}, 201)
    else:
        return make_response({'message': 'Nothing to stop.'}, 201)


@BP.route("/search", methods=["POST"])
def query():
    payload = request.json or request.form
    current_app.logger.info('the payload from frontend: {}'.format(str(payload.to_dict())))
    form = QueryForm(request.form)
    if not form.validate():
        message = ''
        for error, info in form.errors.items():
            message += error + ': ' + str(info) + '\n'
        current_app.logger.info('Error! form fields not valid! {}'.format(message))
        return make_response({'message': message, 'data': ''}, 201)

    manager = MongoDbManager.get_instance(current_app)

    if manager.get_client() is not None:
        data = manager.query_by_pattern(form.to_dict())
        length = data.count()
        current_app.logger.info('/search : Found {} records. '.format(length))
        return make_response(
            {'message': 'got ' + str(length) + ' result', 'data': '\n'.join([str(record) for record in data[:100]])},
            201)
    else:
        message = 'Fail to get MongoDBManager!'
        current_app.logger.info('/search : Error! ' + message)
        return make_response({'message': message, 'data': ''}, 201)
