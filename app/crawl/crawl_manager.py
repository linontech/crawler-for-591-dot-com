import concurrent.futures
import time
import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from flask import current_app


class CrawlManager(object):
    DELAY = 0.6
    MAX_WORKERS = 10
    ATTEMPT_STOP = False
    RUNNING = False

    def __init__(self):
        pass

    def _create_payloads(self):
        raise NotImplemented

    def job(self, payload, session, app):
        raise NotImplemented

    def call_back_function(self, future, session):
        raise NotImplemented

    def run(self):
        """
        CrawlManager multi-thread
        :return: message
        """
        payloads = self._create_payloads()
        current_app.logger.info(
            f'CrawlManager run() is going to make {len(payloads)} requests. ')
        if not self.RUNNING:
            start = time.time()
            self.ATTEMPT_STOP, self.RUNNING = False, True
            with concurrent.futures.ThreadPoolExecutor(thread_name_prefix='MyCrawler', max_workers=self.MAX_WORKERS) as executor:
                for index in range(0, len(payloads), self.MAX_WORKERS):
                    if self.ATTEMPT_STOP:
                        end = time.time()
                        current_app.logger.info(f'CrawlManager run() stopped by user, spent: {end - start} seconds. ')
                        self.RUNNING = False
                        return 'stopped'
                    with requests.Session() as session:
                        session.mount('https://',
                                      HTTPAdapter(
                                          pool_connections=current_app.config.get('POOL_CONNECTIONS_NUM'),
                                          pool_maxsize=current_app.config.get('POOL_MAXSIZE_NUM')))
                        self._set_csrf_token(session)
                        futures = [
                            executor.submit(self.job, payload, session, current_app._get_current_object())
                            for payload in payloads[index: index + self.MAX_WORKERS]
                        ]
                        for future in concurrent.futures.as_completed(futures):
                            self.call_back_function(future, session)
            end = time.time()
            current_app.logger.info(
                f'CrawlManager run() done spent: {end - start} seconds. ')
            self.RUNNING = False

        return 'finished'

    def _set_csrf_token(self, session):
        """
        :param session:
        :return:
        """
        r = session.get(current_app.config.get('API_ROOT_URL'))
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup.select('meta'):
            if tag.get('name', None) == 'csrf-token':
                csrf_token = tag.get('content')
                session.headers = current_app.config.get('HEADERS')
                session.headers['X-CSRF-TOKEN'] = csrf_token
                current_app.logger.info(f'Found csrf-token ' + csrf_token)
                break
        else:
            current_app.logger.info(f'No csrf-token found')

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

