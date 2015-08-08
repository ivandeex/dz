import os
import json
import traceback
import shutil
import logging

from scrapy import Spider, signals
from scrapy.utils.serialize import ScrapyJSONEncoder
from scrapy.utils import project, log
from twisted.internet import reactor

from .redis import connection
from .redis.httpcache import RedisCacheStorage
from .settings import CustomSettings, ACTION_PARAMETER, DEFAULT_ACTION

CustomSettings.register(
    UPLOAD_INFO_KEY='%(spider)s:upload-info',
    UPLOAD_INFO_RESET=False,
    )


class CustomSpider(Spider):

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop(ACTION_PARAMETER, None)
        self.redis = None
        super(CustomSpider, self).__init__(*args, **kwargs)

    @classmethod
    def update_settings(cls, settings):
        Spider.update_settings(settings)
        custom = CustomSettings(cls.name, settings)
        settings.setdict(custom.as_dict(), custom.priority)
        cls.settings_init = settings

        # reconfigure logging
        logger = logging.root
        logger.removeHandler(logger.handlers[0])
        logger.addHandler(log._get_handler(settings))

    def _set_crawler(self, crawler):
        super(CustomSpider, self)._set_crawler(crawler)
        base_action = crawler.settings.get(ACTION_PARAMETER, DEFAULT_ACTION)
        if getattr(self, 'action', None) is None:
            self.action = base_action
        self.action_list = self.action.split(',')
        self.stats = crawler.stats
        self.debug = crawler.settings.getbool('DEBUG')
        crawler.signals.connect(self.opened, signals.spider_opened)

    def opened(self):
        self.redis_enabled = self.settings.get('STORAGE') == 'redis'
        self.upload_info_key = self.settings.get('UPLOAD_INFO_KEY')
        self.encoder = ScrapyJSONEncoder()
        self.crawler_stopped = False
        self.open_database()

        self._flag_exit = self._flag_stop = True
        for action in self.action_list:
            self._flag_exit = self._flag_stop = False
            self.run_action(action)
        if self._flag_stop:
            reactor.callLater(0, self.crawler.stop)
        if self._flag_exit:
            self.abort(0)

    def closed(self, reason):
        if reason == 'finished':
            self.on_finished()
        else:
            self.close_database()

    def open_database(self):
        if self.redis_enabled:
            self.redis = connection.from_settings(self.settings)

    def close_database(self):
        self.redis = None

    def reset_database(self):
        if self.redis:
            table = self.get_table_name()
            if table:
                self.redis.delete(table)

    def purge_database(self):
        pass

    def get_table_name(self, item=None):
        return getattr(self, 'table_name', self.name + ':items')

    def store_item(self, table, key, data):
        self.redis.hset(table, key, self.encoder.encode(data))

    def get_next_key(self, table=None):
        return self.redis.hlen(table or self.get_table_name()) + 1

    def _process_store_item(self, item):
        process = getattr(self, 'process_store_item', None)
        if not process:
            return
        result = process(item)
        if result is None:
            return
        if not isinstance(result, (tuple, list)):
            result = [result]

        num = len(result)
        assert 1 <= num <= 3, 'Invalid result of process_store_item()'
        if num == 3:
            table, key, data = result
        elif num == 2:
            key, data = result
            table = self.get_table_name(data)
        elif num == 1:
            data = result[0]
            table = self.get_table_name(data)
            key = self.get_next_key(table)

        if key is not None:
            self.store_item(table, key, data)

    def upload_info(self, op, key, data=None):
        if not self.upload_info_key:
            return
        if op == 'get':
            data = self.redis.hget(self.upload_info_key, key)
            if data is not None:
                return json.loads(data)
        if op == 'set':
            self.redis.hset(self.upload_info_key, key, json.dumps(data))

    def clear_redis(self):
        s = self.settings
        del_keys = []
        key = s.get('SCHEDULER_QUEUE_KEY')
        if key:
            del_keys.extend((key, key + '-url'))
        key = s.get('DUPEFILTER_KEY')
        if key:
            del_keys.extend((key, key + '-url'))

        if self.upload_info_key and s.getbool('UPLOAD_INFO_RESET'):
            del_keys.append(self.upload_info_key)

        if del_keys and self.redis_enabled:
            redis = self.redis or connection.from_settings(self.settings)
            redis.delete(*del_keys)

    def clear_cache(self, what=''):
        if what in ('redis', 'all') and self.redis_enabled:
            s = self.settings
            if s.getbool('HTTPCACHE_ENABLED') and s.get('HTTPCACHE_KEY'):
                RedisCacheStorage.clear_all(self)
        if what in ('disk', 'all'):
            for subdir in '', self.settings['HTTPCACHE_DIR']:
                path = os.path.join(project.data_path(subdir), self.name)
                self.logger.debug('Removing %s', path)
                shutil.rmtree(path, ignore_errors=True)

    def finish(self, message=None, stop=False, exit=True):
        self.logger.info(message or 'Done')
        if stop:
            self._flag_stop = True
        if exit:
            self._flag_exit = True

    def stop_crawler(self, message=None, reason='finished'):
        if not self.crawler_stopped:
            self.crawler.engine.close_spider(self, reason='finished')
            if message:
                self.logger.info(message)
            self.crawler_stopped = True

    def abort(self, ret=1):
        os._exit(ret)

    def run_action(self, action):
        self.logger.debug('Action: %s', action)
        try:
            method = getattr(self, 'on_' + action)
        except AttributeError:
            self.logger.error('Action unimplemented: %s', action)
            self.abort(1)
        try:
            method()
        except Exception:
            traceback.print_exc()
            self.abort(1)

    def on_all(self):
        self.on_reset(exit=False)
        self.run_action('crawl')

    def on_finished(self):
        self.close_database()

    def on_reset(self, exit=True):
        self.reset()
        self.reset_database()
        self.clear_redis()
        self.clear_cache('redis')
        self.finish('State cleared', stop=exit, exit=exit)

    def reset(self):
        pass

    def on_purge(self, exit=True):
        self.purge()
        self.clear_cache('disk')
        self.purge_database()
        self.on_reset(exit)

    def purge(self):
        pass

    def on_settings(self):
        for name, opt in sorted(self.settings.attributes.items()):
            if opt.priority > 0:  # not default
                print '%s = %s' % (name, opt.value)
        self.finish('Bye')

    def on_crawl(self):
        pass

    def on_excel(self):
        pass

    def on_parse(self):
        pass

    def on_shell(self):
        pass
