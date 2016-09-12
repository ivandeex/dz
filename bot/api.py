import os
import re
import socket
import random
import hashlib
import requests
from urlparse import urljoin
from datetime import datetime
from .utils import logger, merge_ranges

try:
    import cjson
    json_encode = cjson.encode
    json_decode = cjson.decode
except ImportError:
    import json
    json_encode = json.dumps
    json_decode = json.loads


DEFAULT_API_URL = 'http://localhost/dz/api/crawl/'
DEFAULT_SECRET_KEY = 'please change me'
MAX_TIME_DIFF = 900


def naive2api(dt=None):
    if dt is None:
        dt = datetime.utcnow()
    return dt.replace(microsecond=0).strftime('%Y-%m-%d,%H:%M')


def api2naive(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%d,%H:%M')


def api_request(command, params):
    web_server = os.environ.get('SERVER_API_URL', DEFAULT_API_URL)
    secret_key = os.environ.get('SPIDER_SECRET_KEY', DEFAULT_SECRET_KEY)

    req = params.copy()
    req['time'] = naive2api(datetime.utcnow())
    req['rand'] = str(random.randint(100, 999))
    req['host'] = socket.gethostname()
    req['pid'] = str(os.getpid())

    source = '|'.join([req[key] for key in ('time', 'rand', 'host', 'pid')])
    req['digest'] = hashlib.sha1(source + secret_key).hexdigest()

    url = urljoin(web_server, command)
    resp = requests.post(url, json=req)
    assert resp.status_code == 200, 'Invalid response status %d' % resp.status_code
    resp = resp.json()

    diff = (api2naive(resp['time']) - datetime.utcnow()).total_seconds()
    assert abs(diff) < MAX_TIME_DIFF, 'Invalid response time stamp'

    assert re.match(r'^\d\d\d$', req['rand']), 'Invalid response rand'

    source = '%s|%s' % (resp['time'], resp['rand'])
    digest = hashlib.sha1(source + secret_key).hexdigest()
    assert digest == resp['digest'], 'Invalid response digest'

    return resp


def api_send_item(target, start_utc, debug, item):
    try:
        data = item.copy()
        data['crawled_utc'] = naive2api()
        data['updated'] = naive2api(data['updated'])
        data['published'] = naive2api(data['published'])

        resp = api_request('item', dict(target=target, start_utc=start_utc, data=data))
        if not resp['ok']:
            logger.info('Server returned "item" failure: %s', resp['error'])
    except Exception as err:
        logger.info('Item sending failed: %r', err)
        if debug:
            raise


def api_send_complete(target, start_utc, debug, ids):
    try:
        str_ids = merge_ranges(sorted(ids))
        resp = api_request('complete', dict(target=target, start_utc=start_utc, ids=str_ids))
        if not resp['ok']:
            logger.info('Server returned "complete" failure: %s', resp['error'])
    except Exception as err:
        logger.info('Item sending failed: %r', err)
        if debug:
            raise
