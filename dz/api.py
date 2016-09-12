import re
import random
import hashlib
import logging
import pytz
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F
from django.utils import timezone
from django.conf import settings
from . import models

try:
    import cjson
    json_encode = cjson.encode
    json_decode = cjson.decode
except ImportError:
    import json
    json_encode = json.dumps
    json_decode = json.loads


MAX_TIME_DIFF = 900

logger = logging.getLogger(__name__)


def time2api(dt):
    assert not timezone.is_naive(dt), 'Invalid naive time'
    naive_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return naive_utc.strftime('%Y-%m-%d,%H:%M')


def api2time(time_str, tzname=None):
    dt = timezone.datetime.strptime(time_str, '%Y-%m-%d,%H:%M')
    if tzname == 'UTC':
        return dt.replace(tzinfo=timezone.utc)
    if not tzname:
        tzname = settings.SPIDER_TIME_ZONE
    # Important! Use pytz.tzinfo.localize instead of datetime.astimezone!
    dt = pytz.timezone(tzname).localize(dt)
    # Always return UTC
    return dt.astimezone(timezone.utc)


def parse_request(request, command):
    assert request.method == 'POST', 'Invalid request type'
    assert request.content_type == 'application/json', 'Invalid content type'

    unicode_body = request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
    req = json_decode(unicode_body)

    if settings.DEBUG_API:
        req_cut = req
        if 'data' in req:
            req_cut = req.copy()
            data_cut = req_cut['data'] = req['data'].copy()
            for key, value in data_cut.items():
                if isinstance(value, basestring) and len(value) > 200:
                    data_cut[key] = value[:200] + ' .....'
        logger.debug('request "%s": %s', command, req_cut)

    req_utc = api2time(req['time'], 'UTC').replace(tzinfo=None)
    diff = (datetime.utcnow() - req_utc).total_seconds()
    assert abs(diff) < MAX_TIME_DIFF, 'Invalid request time stamp'

    assert re.match(r'^\d\d\d$', req['rand']), 'Invalid request rand'

    assert req['host'], 'Invalid request host'
    assert req['pid'], 'Invalid request pid'

    source = '|'.join([req[key] for key in ('time', 'rand', 'host', 'pid')])
    digest = hashlib.sha1(source + settings.SPIDER_SECRET_KEY).hexdigest()
    assert digest == req['digest'], 'Invalid request digest'

    return req


def make_response(**resp):
    resp['time'] = time2api(timezone.now().replace(microsecond=0))
    resp['rand'] = str(random.randint(100, 999))

    source = '%s|%s' % (resp['time'], resp['rand'])
    resp['digest'] = hashlib.sha1(source + settings.SPIDER_SECRET_KEY).hexdigest()

    if settings.DEBUG_API:
        logger.debug('API response: %s', resp)
    return HttpResponse(json_encode(resp), content_type='application/json')


def merge_ranges(data):
    res = []
    beg = end = None
    for v in data:
        if end is None:
            beg = end = v
        elif v == end + 1:
            end = v
        else:
            res.append(str(beg) if beg == end else '%d-%d' % (beg, end))
            beg = end = v
    if end is not None:
        res.append(str(beg) if beg == end else '%d-%d' % (beg, end))
    return ','.join(res)


def split_ranges(range_str):
    res = set()
    if range_str:
        for token in range_str.split(','):
            if '-' in token:
                beg, end = token.split('-')
                for val in range(int(beg), int(end) + 1):
                    res.add(val)
            else:
                res.add(int(token))
    return res


def get_model(target):
    assert target in ('news', 'tips'), 'Invalid target'
    model_classes = dict(news=models.News, tips=models.Tip)
    return model_classes[target]


@csrf_exempt
def api_crawl_job(request):
    try:
        req = parse_request(request, 'job')

        resp = {
            'ok': True,
            'found': False,
            'log_level': settings.SPIDER_LOG_LEVEL,
            'load_images': settings.SPIDER_LOAD_IMAGES,
            'userpass': settings.SPIDER_USERPASS,
        }

        crawl = models.Crawl.get_manual_crawl() or models.Crawl.get_auto_crawl()
        if crawl:
            seen_news = ''
            if crawl.target == 'news':
                seen_news = merge_ranges(models.News.get_seen_ids())

            crawl.host = req['host']
            crawl.pid = req['pid']
            crawl.status = 'started'
            crawl.count = 0
            crawl.ended = None
            crawl.save()

            resp['found'] = True
            resp['target'] = crawl.target
            resp['start_utc'] = time2api(crawl.started)
            resp['seen_news'] = seen_news
            resp['page_delay'] = settings.SPIDER_PAGE_DELAY
        return make_response(**resp)

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid job packet: %s', err)
        return make_response(ok=False, found=False, error=repr(err))


@csrf_exempt
def api_crawl_item(request):
    id = None
    try:
        req = parse_request(request, 'item')
        Model = get_model(req['target'])

        data = req['data']
        id = data['id']
        data['crawled'] = api2time(data.pop('crawled_utc'), 'UTC')
        data['updated'] = api2time(data['updated'])
        data['published'] = api2time(data['published'])
        data['archived'] = False

        Model.from_json(data)

        running_crawls = models.Crawl.objects.filter(status__in=['started', 'running'])
        crawl, created = running_crawls.get_or_create(
            started=api2time(req['start_utc'], 'UTC'),
            target=req['target'],
            host=req['host'],
            pid=req['pid'],
        )
        crawl.count = F('count') + 1
        crawl.status = 'running'
        crawl.ended = None
        crawl.save()

        return make_response(ok=True, id=id, target=req['target'])

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid item packet: %s', err)
        return make_response(ok=False, error=repr(err), id=id, target=['target'])


@csrf_exempt
def api_crawl_complete(request):
    try:
        req = parse_request(request, 'complete')

        Model = get_model(req['target'])
        ids = split_ranges(req['ids'])

        # just crawled items become fresh
        Model.objects.filter(id__in=ids).update(archived=False)
        # the remainder becomes archived
        Model.objects.filter(~Q(id__in=ids)).update(archived=True)

        running_crawls = models.Crawl.objects.filter(status__in=['started', 'running'])
        crawl, created = running_crawls.get_or_create(
            target=req['target'],
            started=api2time(req['start_utc'], 'UTC'),
            host=req['host'],
            pid=req['pid'],
        )
        crawl.count = len(ids)
        crawl.status = 'complete'
        crawl.ended = timezone.now()
        crawl.save()

        return make_response(ok=True, target=req['target'])

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid final packet: %s', err)
        return make_response(ok=False, error=repr(err), target=req['target'])
