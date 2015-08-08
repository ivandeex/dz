import os
import time
import logging
from twisted.internet import threads
from scrapy.extensions.httpcache import FilesystemCacheStorage
from scrapy.exceptions import NotConfigured

try:
    from ..utils.sftp import SFTPClient
except ImportError:
    SFTPClient = None

from . import CustomSettings

CustomSettings.register(
    HTTPCACHE_EXPIRATION_SECS=0,
    HTTPCACHE_SFTP_tmpl='',
    )


class SFTPCacheStorage(FilesystemCacheStorage):

    logger = logging.getLogger(__name__)

    def __init__(self, settings):
        if SFTPClient is None:
            raise NotConfigured

        super(SFTPCacheStorage, self).__init__(settings)
        self.sftp_url = settings.get('HTTPCACHE_SFTP')
        if self.sftp_url:
            assert self.sftp_url.startswith('sftp://')
        self.sftp_cli = None
        self.debug = settings.getbool('DEBUG')

    def open_spider(self, spider):
        super(SFTPCacheStorage, self).open_spider(spider)
        if self.sftp_url:
            self.sftp_cli = SFTPClient(self.sftp_url,
                                       local_dir=self.cachedir)
            self.sftp_bg = 'bg=1' in self.sftp_cli.options

    def close_spider(self, spider):
        super(SFTPCacheStorage, self).close_spider(spider)
        if self.sftp_cli:
            self.sftp_cli.close()

    def retrieve_response(self, spider, request):
        res = super(SFTPCacheStorage, self).retrieve_response(spider, request)
        if self.debug:
            rpath = self._get_request_path(spider, request)
            age = -1
            if os.path.exists(os.path.join(rpath, 'pickled_meta')):
                try:
                    age = time.time() - os.stat(rpath).st_mtime
                except IOError:
                    pass
            self.logger.debug(
                'Cache %(state)s (%(age)d > %(exp)d): %(url)s under: %(path)s',
                dict(state='HIT' if res else 'MISS', url=request.url,
                     path=rpath, age=age, exp=self.expiration_secs))
        return res

    def store_response(self, spider, request, response):
        super(SFTPCacheStorage, self).store_response(spider, request, response)
        if not self.sftp_cli:
            return

        rpath = self._get_request_path(spider, request)

        def upload_items():
            for item in ('meta', 'pickled_meta', 'response_headers',
                         'response_body', 'request_headers', 'request_body'):
                self.sftp_cli.upload_file(os.path.join(rpath, item))

        if self.sftp_bg:
            return threads.deferToThread(upload_items)
        else:
            upload_items()
