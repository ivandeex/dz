from .scheduler import Scheduler as RedisScheduler
from .useragent import RedisUserAgentMiddleware
from .httpcache import RedisCacheStorage

from .. import CustomSettings

CustomSettings.register(
    REDIS_URL='redis://',
    REDIS_DIR='%(spider)s:',
    )
