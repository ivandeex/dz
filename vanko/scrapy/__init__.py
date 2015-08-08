from .defaults import DEFAULT_PROJECT_DIR
try:
    import scrapy
    del scrapy
except ImportError:
    pass
else:
    from .helpers import setup_spider, run_spider, setup_stderr
    from .settings import CustomSettings
    from .spider import CustomSpider
    from .crawl import CustomCrawlSpider
    from .item_loader import (
        TFItemLoader, TakeFirstItemLoader, Item, SimpleItem,
        Field, StripField, JoinField, DateTimeField, extract_datetime)
    from .fast_exit import FastExit
    from .show_ip import ShowIP
    from .restart_on import RestartOn
    from .redis import RedisScheduler, RedisCacheStorage
    from .redis import RedisUserAgentMiddleware
    from .pipelines import ItemStorePipeline, EarlyProcessPipeline
    from .sftp_httpcache import SFTPCacheStorage
