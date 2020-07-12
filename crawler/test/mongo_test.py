import mock
import mongomock

from app import app
from crawler.CrawlManager import CrawlManager
from crawler.MongoDbManager import MongoDbManager


@mock.patch('crawler.MongoDbManager.get_client')
@mock.patch('crawler.CrawlManager.CrawlManager._create_payloads')
def test_should_insertion_operate_properly(
        mock_create_payloads, mock_get_client):
    mock_create_payloads.return_value = [{'is_new_list': '1',
                                          'type': '1',
                                          'kind': '0',
                                          'searchtype': 1,
                                          'regionid': '1',
                                          'firstRow': 30,
                                          'totalRows': 12503},
                                         {'is_new_list': '1',
                                          'type': '1',
                                          'kind': '0',
                                          'searchtype': 1,
                                          'regionid': '1',
                                          'firstRow': 30,
                                          'totalRows': 12503},
                                         {'is_new_list': '1',
                                          'type': '1',
                                          'kind': '0',
                                          'searchtype': 1,
                                          'regionid': '1',
                                          'firstRow': 60,
                                          'totalRows': 12503},
                                         ]

    mock_get_client.return_value = mongomock.MongoClient()
    with app.app_context():
        crawl_mgr = CrawlManager.get_instance()
        mongo_mgr = MongoDbManager.get_instance(app)
        result = crawl_mgr.run()
        houses = mongo_mgr.get_client(app).five9one.houses.find()

    assert result == 'finished'
    assert houses.count() == 30 * 3 - crawl_mgr.duplicate_count
