import logging
from time import time
from six.moves import cPickle as pickle
from scrapy.extensions.httpcache import DbmCacheStorage
from scrapy.exceptions import NotConfigured
from . import connection
from .. import CustomSettings

CustomSettings.httpcachestorage_map = {
    'normal': 'vanko.scrapy.sftp_httpcache.SFTPCacheStorage',
    'redis': 'vanko.scrapy.redis.httpcache.RedisCacheStorage',
    }

CustomSettings.register(
    HTTPCACHE_ENABLED=True,
    HTTPCACHE_REDIS_URL='',
    HTTPCACHE_KEY='%(spider)s:httpcache',
    HTTPCACHE_STORAGE_tmpl_map_httpcachestorage='normal',
    )


class RedisCacheStorage(DbmCacheStorage):

    HTTPCACHE_KEY = 'httpcache-%(spider)s'
    logger = logging.getLogger(__name__)

    def __init__(self, settings):
        try:
            from redis import from_url
        except ImportError:
            raise NotConfigured
        else:
            redis_url = settings.get('HTTPCACHE_REDIS_URL')
            if redis_url:
                self.redis = from_url(redis_url)
            else:
                self.redis = connection.from_settings(settings)
            self.key_tmpl = settings.get('HTTPCACHE_KEY', self.HTTPCACHE_KEY)
            self.expiration_secs = settings.getint('HTTPCACHE_EXPIRATION_SECS')

    def open_spider(self, spider):
        key = self.key_tmpl % {'spider': spider.name}
        self.data_hash = key + '-data'
        self.time_hash = key + '-time'
        self.logger.debug('Redis cache opened')

    def close_spider(self, spider):
        pass

    def store_response(self, spider, request, response):
        key = self._request_key(request)
        data = {
            'status': response.status,
            'url': response.url,
            'headers': dict(response.headers),
            'body': response.body,
        }
        ts = str(time())
        self.redis.hset(self.data_hash, key, pickle.dumps(data, protocol=2))
        self.redis.hset(self.time_hash, key, ts)
        self.logger.debug('Store %s in redis cache', response.url)

    def _read_data(self, spider, request):
        key = self._request_key(request)
        ts = self.redis.hget(self.time_hash, key)
        if ts is None:
            return  # not found
        if 0 < self.expiration_secs < time() - float(ts):
            return  # expired
        data = self.redis.hget(self.data_hash, key)
        if data is None:
            return  # key is dropped
        data = pickle.loads(data)
        self.logger.debug('Retrieve %s from redis cache', data['url'])
        return data

    def _clear(self):
        self.redis.delete(self.time_hash, self.data_hash)

    @classmethod
    def clear_all(cls, spider):
        cache = cls(spider.crawler.settings)
        cache.open_spider(spider)
        cache._clear()
