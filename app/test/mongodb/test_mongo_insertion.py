import mock
import mongomock

from app import create_app
from app.crawl.house_crawler import HouseCrawler
from app.mongodb.mongodb_manager import MongoDbManager


@mock.patch('app.mongodb.mongodb_manager.MongoDbManager.get_client')
@mock.patch('app.crawl.house_crawler.HouseCrawler._create_payloads')
def test_should_insertion_operate_properly(mock_create_payloads, mock_get_client):
    mock_create_payloads.return_value = [
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
    app = create_app()
    with app.app_context():
        crawl_mgr = HouseCrawler.get_instance()
        mongo_mgr = MongoDbManager.get_instance()
        result = crawl_mgr.run()
        houses = mongo_mgr.get_client().five9one.houses.find()

    assert result == 'finished'
    assert houses.count() == 30 * 3 - crawl_mgr.duplicate_count
