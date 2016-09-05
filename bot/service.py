import os
import logging
from time import sleep
from .utils import logger
from .api import api_request
from .news import NewsSpider
from .tips import TipsSpider


DEFAULT_POLL_SECONDS = 50


class Service(object):
    def __init__(self):
        self.poll_seconds = int(os.environ.get('POLL_SECONDS', DEFAULT_POLL_SECONDS))
        self.debug = bool(int(os.environ.get('DEBUG', False)))

    def run(self):
        logger.info('Service running')
        while 1:
            sleep(self.poll_seconds)
            try:
                resp = api_request('job', {})
                logger.setLevel(logging.getLevelName(resp['log_level']))
                if resp['found']:
                    env = {
                        'START_TIME': resp['start_time'],
                        'SEEN_NEWS': resp['seen_news'],
                        'PAGE_DELAY': resp['page_delay'],
                        'LOAD_IMAGES': resp['load_images'],
                        'USERPASS': resp['userpass'],
                    }
                    self.action(resp['target'], env)
            except Exception as err:
                logger.error('Service error: %r', err)
                if self.debug:
                    raise

    @staticmethod
    def action(target, env={}):
        assert target in ('news', 'tips'), 'Invalid target "%s"' % target
        Spider = dict(news=NewsSpider, tips=TipsSpider)[target]
        final_env = os.environ.copy()
        final_env.update(env)
        spider = Spider(final_env)
        try:
            spider.run()
            spider.end()
        finally:
            spider.close()
