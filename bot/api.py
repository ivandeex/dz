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


DEFAULT_WEB_SERVER = 'http://dz.com/dz/api/crawl/'
DEFAULT_SECRET_KEY = 'please change me'


def dt2json(dt):
    return str(dt.replace(microsecond=0))


def json2dt(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')


def api_request(command, params):
    web_server = os.environ.get('WEB_SERVER', DEFAULT_WEB_SERVER)
    secret_key = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)

    req = params.copy()
    req['time'] = dt2json(datetime.utcnow())
    req['rand'] = str(random.randint(100, 999))
    req['host'] = socket.gethostname()
    req['pid'] = str(os.getpid())

    source = '|'.join([req[key] for key in ('time', 'rand', 'host', 'pid')])
    req['digest'] = hashlib.sha1(source + secret_key).hexdigest()

    url = urljoin(web_server, command)
    resp = requests.post(url, json=req)
    resp = resp.json()

    diff = (json2dt(resp['time']) - datetime.utcnow()).total_seconds()
    assert abs(diff) < 600, 'Invalid response time stamp'

    assert re.match(r'^\d\d\d$', req['rand']), 'Invalid response rand'

    source = '%s|%s' % (resp['time'], resp['rand'])
    digest = hashlib.sha1(source + secret_key).hexdigest()
    assert digest == resp['digest'], 'Invalid response digest'

    return resp


def api_send_item(target, start_time, debug, item):
    try:
        data = item.copy()
        data['crawled'] = dt2json(datetime.utcnow())
        data['updated'] = dt2json(data['updated'])
        data['published'] = dt2json(data['published'])

        resp = api_request('item', dict(target=target, start_time=start_time, data=data))
        if not resp['ok']:
            logger.info('Server returned "item" failure: %s', resp['error'])
    except Exception as err:
        logger.info('Item sending failed: %r', err)
        if debug:
            raise


def api_send_complete(target, start_time, debug, ids):
    try:
        str_ids = merge_ranges(sorted(ids))
        resp = api_request('complete', dict(target=target, start_time=start_time, ids=str_ids))
        if not resp['ok']:
            logger.info('Server returned "complete" failure: %s', resp['error'])
    except Exception as err:
        logger.info('Item sending failed: %r', err)
        if debug:
            raise
