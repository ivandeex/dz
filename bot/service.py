import os
import logging
from time import sleep
import bot
from .utils import logger
from .api import api_check_job, naive2api
from .news import NewsSpider
from .tips import TipsSpider


DEFAULT_POLL_SECONDS = 50


class Service(object):
    def __init__(self):
        self.poll_seconds = int(os.environ.get('POLL_SECONDS', DEFAULT_POLL_SECONDS))
        self.debug = bool(int(os.environ.get('DEBUG', False)))

    def run(self):
        logger.info('Service running, v%s', bot.version)
        while True:
            sleep(self.poll_seconds)
            try:
                resp = api_check_job()
                logger.setLevel(logging.getLevelName(resp['log_level']))
                if resp['found']:
                    env = {
                        'START_UTC': resp['start_utc'],
                        'SEEN_NEWS': resp['seen_news'],
                        'LIMIT_NEWS': resp['limit_news'],
                        'PAGE_DELAY': resp['page_delay'],
                        'LOAD_IMAGES': resp['load_images'],
                        'USERPASS': (resp['userpass'] + '====').decode('base64'),
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
        start_utc = final_env.setdefault('START_UTC', naive2api())
        logger.info('Commence %s crawl from %s (UTC)', target, start_utc)
        spider = Spider(final_env)
        try:
            spider.run()
        finally:
            spider.close()
