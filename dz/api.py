import re
import random
import hashlib
import logging
import pytz
import json
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, F
from django.utils import timezone
from django.conf import settings
from .config import spider_config
from .ranges import merge_ranges, split_ranges
from . import models


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
        tzname = spider_config('TIME_ZONE')
    # Important! Use pytz.tzinfo.localize instead of datetime.astimezone!
    dt = pytz.timezone(tzname).localize(dt)
    # Always return UTC
    return dt.astimezone(timezone.utc)


def parse_request(request, command):
    assert request.method == 'POST', 'Invalid request type'
    assert request.META['CONTENT_TYPE'] == 'application/json', 'Invalid content type'

    unicode_body = request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
    req = json.loads(unicode_body)

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
    digest = hashlib.sha1(source + spider_config('SECRET_KEY')).hexdigest()
    assert digest == req['digest'], 'Invalid request digest'

    # Real host name can be too long to fit in the model.
    # As it is just for reference, we truncate it without hesitation.
    max_len = models.Crawl._meta.get_field('host').max_length
    if len(req['host']) > max_len:
        req['host'] = req['host'][:max_len - 3] + '...'

    return req


def make_response(**resp):
    resp['time'] = time2api(timezone.now().replace(microsecond=0))
    resp['rand'] = str(random.randint(100, 999))

    source = '%s|%s' % (resp['time'], resp['rand'])
    resp['digest'] = hashlib.sha1(source + spider_config('SECRET_KEY')).hexdigest()

    if settings.DEBUG_API:
        logger.debug('API response: %s', resp)
    return HttpResponse(json.dumps(resp), content_type='application/json')


def get_model(target):
    assert target in ('news', 'tips'), 'Invalid target'
    model_classes = dict(news=models.News, tips=models.Tip)
    return model_classes[target]


@require_POST
@csrf_exempt
def api_crawl_job(request):
    try:
        req = parse_request(request, 'job')

        resp = {
            'ok': True,
            'found': False,
            'log_level': spider_config('LOG_LEVEL'),
            'load_images': spider_config('LOAD_IMAGES'),
            'userpass': spider_config('USERPASS').encode('base64').rstrip('\n='),
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
            resp['limit_news'] = spider_config('LIMIT_NEWS')
            resp['page_delay'] = spider_config('PAGE_DELAY')
        return make_response(**resp)

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid job packet: %s', err)
        return make_response(ok=False, found=False, error=repr(err))


@require_POST
@csrf_exempt
def api_crawl_item(request):
    target = pk = None
    try:
        req = parse_request(request, 'item')
        target = req['target']
        Model = get_model(target)

        data = req['data']
        pk = data['pk']
        data['crawled'] = api2time(data.pop('crawled_utc'), 'UTC')
        data['updated'] = api2time(data['updated'])
        data['published'] = api2time(data['published'])
        data['archived'] = False

        Model.from_json(data)

        crawl = models.Crawl.from_json(req)
        crawl.count = F('count') + 1
        crawl.status = 'running'
        crawl.ended = None
        crawl.save()

        return make_response(ok=True, pk=pk, target=target)

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid item packet: %r', err)
        return make_response(ok=False, error=repr(err), pk=pk, target=target)


@require_POST
@csrf_exempt
def api_crawl_complete(request):
    target = None
    try:
        req = parse_request(request, 'complete')
        target = req['target']
        Model = get_model(target)
        ids = split_ranges(req['ids'])

        # just crawled items become fresh
        Model.objects.filter(id__in=ids).update(archived=False)
        # the remainder becomes archived
        Model.objects.filter(~Q(id__in=ids)).update(archived=True)

        crawl = models.Crawl.from_json(req)
        crawl.count = len(ids)
        crawl.status = 'complete'
        crawl.ended = timezone.now()
        crawl.save()

        return make_response(ok=True, target=target)

    except Exception as err:
        if settings.DEBUG:
            raise
        logger.info('Invalid final packet: %r', err)
        return make_response(ok=False, error=repr(err), target=target)
