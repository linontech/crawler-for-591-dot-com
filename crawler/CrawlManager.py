import concurrent.futures
import threading
import time

import requests
from flask import current_app
from requests.adapters import HTTPAdapter

from crawler.crawler import get_houses, get_houses_nums, _set_csrf_token

lock = threading.Lock()


class CrawlManager:
    DELAY = 0.6
    MAX_WORKERS = 3
    DEFAULT_PAYLOAD = {'is_new_list': '1', 'type': '1', 'kind': '0', 'searchtype': 1}
    ATTEMPT_STOP = False
    RUNNING = False
    __instance = None

    def __init__(self):
        raise SyntaxError('can not instance, please use get_instance')

    @classmethod
    def get_instance(cls):
        """
        :return: singleton
        """
        if cls.__instance is None:
            with lock:
                if cls.__instance is None:
                    cls.__instance = object.__new__(cls)

        return cls.__instance

    def run(self, payloads):
        """
        CrawlManager multi-thread
        :param payloads: payloads
        :return: message
        """
        current_app.logger.info(f'CrawlManager run() is going to make {len(payloads)} requests. ')
        if not self.RUNNING:
            start = time.time()
            self.ATTEMPT_STOP = False
            self.RUNNING = True
            with concurrent.futures.ThreadPoolExecutor(thread_name_prefix='MyCrawler', max_workers=self.MAX_WORKERS) as executor:
                for index in range(0, len(payloads), self.MAX_WORKERS):
                    if self.ATTEMPT_STOP:
                        end = time.time()
                        current_app.logger.info(f'CrawlManager run() stopped and spent: {end - start} seconds. ')
                        self.RUNNING = False
                        return 'stopped'
                    with requests.Session() as session:
                        session.mount('https://', HTTPAdapter(
                            pool_connections=current_app.config.get('POOL_CONNECTIONS_NUM'),
                            pool_maxsize=current_app.config.get('POOL_MAXSIZE_NUM')))
                        _set_csrf_token(session, current_app._get_current_object())
                        futures = [executor.submit(get_houses, payload, session, current_app._get_current_object())
                                   for payload in payloads[index: index + self.MAX_WORKERS]]
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                future.result()  # = resulted_ids
                            except Exception as e:
                                current_app.logger.error('CrawlManager run() error: ', e)
            end = time.time()
            current_app.logger.info(f'CrawlManager run() done spent: {end - start} seconds. ')
            self.RUNNING = False

        return 'finished'

    def stop(self):
        """
        stop function
        :return: true for successful stopped
        """
        if not self.RUNNING:
            return False
        while self.RUNNING:
            self.ATTEMPT_STOP = True
        return True

    def is_running(self):
        """
        check status of CrawlManager
        :return: status
        """
        return self.RUNNING

    def create_payloads(self):
        """
        create payloads for 台北1 新北3
        :return: payloads for crawling
        """
        each_page_num = 30
        payloads = []
        for region_id in ['1', '3']:
            self.DEFAULT_PAYLOAD['regionid'] = region_id
            total_rows = get_houses_nums(self.DEFAULT_PAYLOAD)
            current_app.logger.info('Found {} houses for crawling'.format(total_rows))
            for i in range(each_page_num, total_rows + 1, each_page_num):
                payload = self.DEFAULT_PAYLOAD.copy()
                payload['firstRow'] = i
                payload['totalRows'] = total_rows
                payloads.append(payload)

        return payloads
