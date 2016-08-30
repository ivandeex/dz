import random
import hashlib
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F
from django.utils import timezone
from django.template.response import TemplateResponse
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

    res = json_decode(request.body.decode(request.encoding or settings.DEFAULT_CHARSET))
    meta = res.pop('meta')

    ref_digest = meta.pop('digest', '')
    digest_src = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    digest = hashlib.sha1(digest_src + settings.BOT_SECRET_KEY).hexdigest()
    assert digest == ref_digest, 'Invalid digest'

    return res, meta


def prepare_api_response():
    now = timezone.now().replace(microsecond=0)
    meta = dict(utc=str(now.astimezone(timezone.utc)), rand=str(random.randint(1, 99)))
    digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    meta['digest'] = hashlib.sha1(digest + settings.BOT_SECRET_KEY).hexdigest()
    return meta, now


@csrf_exempt
def api_spider_run(request):
    my_meta, now = prepare_api_response()

    try:
        res, meta = parse_api_request(request)
        type_ = meta.get('type', '') or 'manual'
        action = ''
        env = {}
        data = dict(host=meta['host'], ipaddr=meta['ipaddr'], pid=meta['pid'],
                    status='started', started=now)

        if type_ == 'auto':
            action = data['action'] = meta['action']
            data['type'] = 'auto'
            models.Crawl.objects.create(**data)
        else:
            crawl = models.Crawl.objects.filter(status='waiting').order_by('pk').first()
            if crawl:
                action = crawl.action
                data['type'] = 'manual'
                for field, value in data.items():
                    setattr(crawl, field, value)
                crawl.save()

        if action:
            seen_news_pk = (models.News.objects.distinct('pk').order_by('pk')
                            .values_list('pk', flat=True))
            seen_news_str = ','.join(str(pk) for pk in seen_news_pk)
            env = dict(NEWS_TO_SKIP=seen_news_str,
                       STARTTIME=str(data['started']),
                       WITH_IMAGES=0,
                       DOWNLOAD_DELAY=30,
                       LOG_LEVEL=settings.SPIDER_LOG_LEVEL)

        response = dict(okay=True, action=action, env=env, meta=my_meta)

    except Exception as err:
        response = dict(okay=False, error=repr(err), meta=my_meta)

    return HttpResponse(json_encode(response), content_type='application/json')


def json2datetime(time_str):
    dt = timezone.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    return timezone.make_aware(dt)  # naive -> django timezone (ljubljana)


@csrf_exempt
def api_spider_results(request):
    my_meta, now = prepare_api_response()

    try:
        res, meta = parse_api_request(request)
        start_time = json2datetime(meta['starttime'])
        action = meta.get('action', '') or 'unnamed'
        status = res.get('status', 'unknown')
        counts = dict(tips=0, news=0)

        for name, model in [('tips', models.Tip), ('news', models.News)]:
            pk_set = set()

            for item in res.get(name, []):
                item['archived'] = 'fresh'

                for time in ('crawled', 'updated', 'published'):
                    if time in item:
                        item[time] = json2datetime(item[time]) if item[time] else None

                pk = int(item.pop('pk'))
                can_insert = ('url' in item or 'details_url' in item)
                if can_insert:
                    obj = model.objects.get_or_create(pk=pk)
                else:
                    obj = models.objects.get(pk=pk)

                for field, value in item.items():
                    setattr(obj, field, value)
                obj.save()

                pk_set.add(pk)
                counts[name] += 1

            if counts[name] > 1:
                model.objects(~Q(pk__in=pk_set)).update(archived='archived')

        try:
            c = models.Crawl.get(host=meta['host'], action=action, started=start_time)
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

        c.started = start_time
        if status != 'partial':
            c.ended = timezone.now().replace(microsecond=0)
        c.save()

        response = dict(okay=True, meta=my_meta)

    except Exception as err:
        logging.getLogger(__name__).info('Invalid message from spider: %s', err)
        response = dict(okay=False, error=repr(err), meta=my_meta)

    return HttpResponse(json_encode(response), content_type='application/json')
