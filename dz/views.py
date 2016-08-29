import random
import hashlib
import logging
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F
from django.template.response import TemplateResponse
from django.conf import settings
from . import models

try:
    import cjson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json


def index(request):
    usernames = models.User.objects.order_by('username').values('username')
    context = {
        'csv_usernames': ', '.join(x['username'] for x in usernames),
        'server_name': request.get_host(),
    }
    return TemplateResponse(request, 'dz/welcome.html', context)


def parse_api_request(request):
    assert request.method == 'POST', 'Invalid request type'
    assert request.content_type == 'application/json', 'Invalid content type'

    res = json.loads(request.body.decode(request.encoding or settings.DEFAULT_CHARSET))
    meta = res.pop('meta')

    ref_digest = meta.pop('digest', '')
    digest_src = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    digest = hashlib.sha1(digest_src + settings.BOT_SECRET_KEY).hexdigest()
    assert digest == ref_digest, 'Invalid digest'

    return res, meta


def prepare_api_response():
    utc = datetime.utcnow().replace(microsecond=0)
    meta = dict(utc=str(utc), rand=str(random.randint(1, 99)))
    digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    meta['digest'] = hashlib.sha1(digest + settings.BOT_SECRET_KEY).hexdigest()
    return meta, utc


@csrf_exempt
def api_spider_run(request):
    my_meta, utc = prepare_api_response()

    try:
        res, meta = parse_api_request(request)
        type_ = meta.get('type', '') or 'manual'
        action = ''
        env = {}
        data = dict(host=meta['host'], ipaddr=meta['ipaddr'], pid=meta['pid'],
                    status='started', started=str(utc),
                    news=0, tips=0)

        if type_ == 'auto':
            action = meta['action']
            models.Crawl.objects.create(type=type_, action=action, news=0, tips=0)
        else:
            c = models.Crawl.objects.filter(status='waiting').order_by('pk').first()
            if c:
                action = c.action
                c.type = 'manual'
                c.save()

        if action:
            seen_news_pk = (models.News.objects.distinct('pk').order_by('pk')
                            .values_list('pk', flat=True))
            seen_news_str = ','.join(str(pk) for pk in seen_news_pk)
            env = dict(NEWS_TO_SKIP=seen_news_str,
                       STARTTIME=data['started'],
                       WITH_IMAGES=0,
                       DOWNLOAD_DELAY=30,
                       LOG_LEVEL=settings.SPIDER_LOG_LEVEL)

        response = dict(okay=True, action=action, env=env, meta=my_meta)
    except Exception as err:
        response = dict(okay=False, error=repr(err), meta=my_meta)
    return HttpResponse(json.dumps(response), content_type='application/json')


@csrf_exempt
def api_spider_results(request):
    my_meta, utc = prepare_api_response()

    try:
        res, meta = parse_api_request(request)
        counts = dict(tips=0, news=0)
        action = meta.get('action', '') or 'unnamed'
        status = res.get('status', 'unknown')

        for name, model in [('tips', models.Tip), ('news', models.News)]:
            pk_set = set()

            for item in res.get(name, []):
                for time in ('crawled', 'updated', 'published'):
                    if time in item:
                        if item[time]:
                            item[time] = datetime.strptime(item[time], '%Y-%m-%d %H:%M:%S')
                        else:
                            item[time] = None
                item['archived'] = 'fresh'

                pk = int(item.pop('pk'))
                can_insert = ('url' in item or 'details_url' in item)
                if can_insert:
                    obj = model.objects.get_or_create(pk=pk)
                else:
                    obj = models.objects.get(pk=pk)

                for field, val in item.items():
                    setattr(obj, field, val)
                obj.save()

                pk_set.add(pk)
                counts[name] += 1

            if counts[name] > 1:
                model.objects(~Q(pk__in=pk_set)).update(archived='archived')

        try:
            c = models.Crawl.get(host=meta['host'],
                                 action=action,
                                 started=str(meta['starttime']))
            if status == 'partial':
                c.news = F('news') + counts['news']
                c.tips = F('tips') + counts['tips']
            else:
                c.news = counts['news']
                c.tips = counts['tips']
        except models.Crawl.DoesNotExist:
            c = models.Crawl.create(news=counts['news'], tips=counts['tips'])

        c.host = meta['host']
        c.action = action

        c.ipaddr = meta['ipaddr']
        c.pid = meta['pid']
        c.status = status

        c.started = str(meta['starttime'])
        if status != 'partial':
            c.ended = datetime.utcnow().replace(microsecond=0)
        c.save()

        response = dict(okay=True, meta=my_meta)

    except Exception as err:
        logging.getLogger(__name__).info('Invalid message from spider: %s', err)
        response = dict(okay=False, error=repr(err), meta=my_meta)

    return HttpResponse(json.dumps(response), content_type='application/json')
