import os
import socket
import random
import hashlib
import requests
from urlparse import urljoin
from datetime import datetime


getenv = os.environ.get

WEB_SERVER = getenv('WEB_SERVER', 'http://dz.more.vanko.me/dz/api/spider/')
SECRET_KEY = getenv('SECRET_KEY', 'kLIuJ_dvoznak2016_v4')


def send_partial_news(logger, news, action_list, starttime, last=0):
    news = news[:]
    if last > 0:
        last = min(len(news), last)
        news = news[-last:]
    logger.debug('Sending partial results')
    try:
        send_results(logger, news, [], action_list, starttime, 'partial')
    except Exception as err:
        logger.info('Sending choked: %s', err)


def send_results(logger, news, tips, action_list, starttime, status):
    datas = dict(news=news, tips=tips)
    for name in sorted(datas.keys()):
        arr = datas[name]
        for no, item in enumerate(arr):
            item = dict(item)
            for date in ('crawled', 'updated', 'published'):
                if hasattr(item, date):
                    item[date] = str(item[date].replace(microsecond=0))
                if item.get(date, None):
                    item[date] = str(item[date].replace(microsecond=0))
            arr[no] = dict(item)
    action = ','.join([a for a in action_list if a in datas])
    api_request(logger=logger, action=action, request='results', starttime=starttime,
                status=status, news=news, tips=tips)


def api_request(logger, action, request, starttime=None, type=None, **kwargs):
    web_server = WEB_SERVER
    secret = SECRET_KEY
    if not (web_server and secret):
        print 'Requests not active'
        return

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
    meta['digest'] = hashlib.sha1(digest + SECRET_KEY).hexdigest()
    data = kwargs.copy()
    data['meta'] = meta
    status = data.get('status', 'status')

    url = urljoin(web_server, request)
    try:
        res = requests.post(url, json=data).json()
        meta = res.pop('meta', {})
        ref_digest = meta.pop('digest', '')
        digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
        assert hashlib.sha1(digest + SECRET_KEY).hexdigest() == ref_digest
        if logger:
            logger.info('Webserver returned %r for %r (%s)',
                        res, request, status)
        return res
    except Exception as err:
        if logger:
            logger.info('Webserver failed with %r for %r', err, request)
        else:
            print 'Webserver failed with %r for %r' % (err, request)
