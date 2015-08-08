import re
import logging
import pkgutil
from random import randint
from scrapy import signals

from . import connection
from .. import CustomSettings

CustomSettings.register(
    USERAGENT_ENABLED=True,
    USERAGENT_RANDOM=-1,
    USERAGENT_KEY='%(spider)s:user-agent-seq',
    )


class RedisUserAgentMiddleware(object):
    """This downloader middleware rotates user agent on each restart"""

    logger = logging.getLogger(__name__.rpartition('.')[2])
    _singleton = None

    def __init__(self, settings):
        self.settings = settings
        self.enabled = settings.getbool('USERAGENT_ENABLED')

        randomize = settings.getint('USERAGENT_RANDOM')
        if randomize < 0:
            self.randomize = settings.get('STORAGE') != 'redis'
        else:
            self.randomize = bool(randomize)

        self._ua_list = None
        self._user_agent = None
        self.__class__._singleton = self

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        return o

    @classmethod
    def get_global_user_agent(cls, spider):
        return cls._singleton.get_user_agent(spider)

    def get_ua_list(self):
        if self._ua_list is None:
            ua_list = self.settings.getlist('USERAGENT_LIST', [])
            if not ua_list:
                data = pkgutil.get_data(__package__, 'user_agents.xml')
                for line in data.splitlines():
                    mo = re.search(r'useragent="([^"]+)"', line)
                    if mo:
                        ua_list.append(mo.group(1).strip())
            self._ua_list = ua_list
            self.logger.debug('Pulled %d user agents', len(ua_list))

        return self._ua_list

    def _get_redis_index(self, spider):
        try:
            redis = connection.from_settings(self.settings)
            default_key = 'useragent-seq-%(spider)s'
            key = self.settings.get('USERAGENT_KEY', default_key)
            if '%(spider)s' in key:
                assert spider, 'get_user_agent() requires a spider!'
                key = key % {'spider': spider.name}
            return redis.incr(key)
        except Exception as err:
            self.logger.info('Cannot get User-Agent from redis: %s', err)

    def get_user_agent(self, spider=None):
        if self.enabled and self._user_agent is None:
            ua_list = self.get_ua_list()
            ua_num = len(ua_list)
            randomize = self.randomize
            if not randomize:
                index = self._get_redis_index(spider)
                if index is None:
                    randomize = True
            if randomize:
                index = randint(0, ua_num)
            user_agent = ua_list[(index + ua_num - 1) % ua_num]
            self._user_agent = getattr(spider, 'user_agent', user_agent)

        return self._user_agent

    def spider_opened(self, spider):
        user_agent = self.get_user_agent(spider)
        if user_agent:
            self.logger.info('User-Agent: %s', user_agent)

    def process_request(self, request, spider):
        user_agent = self.get_user_agent()
        if user_agent:
            request.headers.setdefault('User-Agent', user_agent)
