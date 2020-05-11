import concurrent.futures
import threading
import time
from flask import current_app

from crawler.crawler import get_houses, get_houses_nums

lock = threading.Lock()


class CrawlManager:
    DELAY = 0.6
    MAX_WORKERS = 5
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
        """
        current_app.logger.info(f'CrawlManager run() is going to make {len(payloads)} requests. ')
        if not self.RUNNING:
            start = time.time()
            self.ATTEMPT_STOP = False
            self.RUNNING = True
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                for index in range(0, len(payloads), self.MAX_WORKERS):
                    if self.ATTEMPT_STOP:
                        end = time.time()
                        current_app.logger.info(f'get_houses() stopped and spent: {end - start} seconds. ')
                        self.RUNNING = False
                        return
                    futures = [executor.submit(get_houses, payload, current_app._get_current_object())
                               for payload in payloads[index: index+5]]
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result_ids = future.result()
                        except Exception as e:
                            current_app.logger.error('get_houses() error: ', e)
                        else:
                            current_app.logger.info('get_houses() and save success ' + str(result_ids))
            end = time.time()
            current_app.logger.info(f'get_houses() done spent: {end - start} seconds. ')
            self.RUNNING = False

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

    def check_status(self):
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
