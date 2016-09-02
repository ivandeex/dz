import os
import socket
import random
import hashlib
import requests
from urlparse import urljoin
from datetime import datetime
from .utils import logger

DEFAULT_WEB_SERVER = 'http://dz.more.vanko.me/dz/api/spider/'
DEFAULT_SECRET_KEY = 'kLIuJ_dvoznak2016_v4'


def send_partial_news(news, starttime, last=0):
    news = news[:]
    if last:
        last = min(len(news), last)
        news = news[-last:]
    logger.debug('Sending partial results')
    try:
        send_results(news, [], 'news', starttime, 'partial')
    except Exception as err:
        logger.info('Sending choked: %s', err)


def send_results(news, tips, action, starttime, status):
    datas = dict(news=news, tips=tips)
    for name in sorted(datas.keys()):
        arr = datas[name]
        for no, item in enumerate(arr):
            item = dict(item)
            for date in ('crawled', 'updated', 'published'):
                if item.get(date, None):
                    item[date] = str(item[date].replace(microsecond=0))
            arr[no] = dict(item)
    api_request(action, 'results', starttime, status=status, news=news, tips=tips)


def api_request(action, request, starttime=None, type=None, **kwargs):
    web_server = os.environ.get('WEB_SERVER', DEFAULT_WEB_SERVER)
    secret = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)
    assert web_server and secret, 'Requests not active'

    meta = {}
    meta['action'] = action
    meta['type'] = str(type or '')
    meta['pid'] = str(os.getpid())
    meta['stamp'] = str(datetime.utcnow().replace(microsecond=0))
    meta['starttime'] = str(starttime or meta['stamp'])
    meta['host'] = socket.gethostname()
    meta['ipaddr'] = socket.gethostbyname(meta['host'])
    meta['rand'] = str(random.randint(1, 99))

    digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    meta['digest'] = hashlib.sha1(digest + secret).hexdigest()
    data = kwargs.copy()
    data['meta'] = meta
    status = data.get('status', 'status')

    url = urljoin(web_server, request)
    try:
        res = requests.post(url, json=data).json()
        meta = res.pop('meta', {})
        ref_digest = meta.pop('digest', '')
        digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
        assert hashlib.sha1(digest + secret).hexdigest() == ref_digest
        if logger:
            logger.info('Webserver returned %r for %r (%s)',
                        res, request, status)
        return res
    except Exception as err:
        if logger:
            logger.info('Webserver failed with %r for %r', err, request)
        else:
            print 'Webserver failed with %r for %r' % (err, request)
