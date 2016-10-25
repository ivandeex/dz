import re
import requests
import json as json_
from mock import patch
from django.test import tag, override_settings
from django.urls import reverse
from dz import models
from bot import api as bot_api
from . import base, factories


@tag('api')
@override_settings(DEBUG_API=False)
class ApiTests(base.BaseDzTestCase):
    LOG_PROTOCOL = False    # True = log protocol messages
    RAISE_ON_ERROR = True   # True = raise bot protocol errors

    @models.Schedule.suspend_logging
    def setUp(self):
        super(ApiTests, self).setUp()

        # Remove all manual/auto crawl jobs, else they interfere with test logic.
        models.Schedule.objects.all().delete()
        models.Crawl.objects.all().delete()

        # Patch bot API layer to call into server API directly.
        self._saved_requests_post = requests.post
        requests.post = self._requests_post_wrapper

        self._saved_default_api_url = bot_api.DEFAULT_API_URL
        # Remove the API endpoint URL part:
        crawl_job_url = reverse('dz:api-job')
        bot_api.DEFAULT_API_URL = re.sub(r'[^/]+/?$', '', crawl_job_url)

    def tearDown(self):
        super(ApiTests, self).tearDown()
        requests.post = self._saved_requests_post
        bot_api.DEFAULT_API_URL = self._saved_default_api_url

    def _requests_post_wrapper(self, url, json):
        if self.LOG_PROTOCOL:
            print 'request to {}: {}'.format(url, json)
        response = self.client.post(url, json_.dumps(json),
                                    content_type='application/json')
        if self.LOG_PROTOCOL:
            print 'response: {}'.format(json_.loads(response.content))
        return response

    def test_api_rejects_non_post_requests(self):
        for endpoint in ('api-job', 'api-item', 'api-complete'):
            response = self.client.get(reverse('dz:%s' % endpoint))
            self.assertEquals(response.status_code, 405)

    @models.Schedule.suspend_logging
    def test_api_can_check_for_jobs(self):
        resp = bot_api.api_check_job()
        self.assertTrue(resp['ok'])
        self.assertFalse(resp['found'])

        result = models.Crawl.add_manual_crawl('news')
        self.assertNotEquals(result, 'refused')

        resp = bot_api.api_check_job()
        self.assertTrue(resp['found'])
        self.assertEquals(resp['target'], 'news')

        result = models.Crawl.add_manual_crawl('tips')
        self.assertNotEquals(result, 'refused')

        resp = bot_api.api_check_job()
        self.assertTrue(resp['found'])
        self.assertEquals(resp['target'], 'tips')

        resp = bot_api.api_check_job()
        self.assertFalse(resp['found'])

    def test_api_can_submit_news(self):
        obj = factories.NewsFactory.build()

        item = {}
        for attr, value in obj.__dict__.items():
            if attr[0] != '_' and attr not in ('crawled', 'id'):
                item[attr] = value
        for attr, value in obj.newstext.__dict__.items():
            if attr[0] != '_' and attr not in ('news_id',):
                item['newstext.' + attr] = value

        self.check_item_sending('news', models.News.objects, item)

    def test_api_can_submit_tips(self):
        obj = factories.TipFactory.build()

        item = {}
        for attr, value in obj.__dict__.items():
            if attr[0] != '_' and attr not in ('crawled', 'id'):
                item[attr] = value

        self.check_item_sending('tips', models.Tip.objects, item)

    def test_api_survives_very_long_host_name(self):
        with patch('socket.gethostname') as fake_gethostname:
            long_string = ''.join([chr(ch) * 3 for ch in range(ord('a'), ord('z'))])
            fake_gethostname.return_value = long_string

            self.test_api_can_submit_tips()

            # The crawl record should exist and contain truncated host name:
            crawl = models.Crawl.objects.first()
            self.assertTrue(crawl.host.endswith('...'))
            self.assertTrue(crawl.host.startswith(long_string[:10]))

    @models.Schedule.suspend_logging
    def make_waiting_crawl(self, target):
        models.Crawl.add_manual_crawl(target)
        resp = bot_api.api_check_job()
        self.assertTrue(resp['found'])
        return resp['start_utc']

    def check_item_sending(self, target, objects, item):
        start_utc = self.make_waiting_crawl(target)
        start_count = objects.count()
        pk = item['pk'] = start_count + 1000  # force unique id

        resp = bot_api.api_send_item(target, start_utc, self.RAISE_ON_ERROR, item)
        self.assertTrue(resp['ok'])

        # The crawl record for the object should exist and be valid.
        self.assertEquals(models.Crawl.objects.count(), 1)
        crawl = models.Crawl.objects.first()
        self.assertEquals(crawl.target, target)
        self.assertEquals(crawl.count, 1)
        self.assertEquals(crawl.status, 'running')

        # The new object should exist in database and marked with archived=False:
        self.assertEquals(objects.count(), start_count + 1)
        self.assertFalse(objects.get(pk=pk).archived)

        self.assertGreater(objects.filter(archived=True).count(), 1)
        self.assertGreater(objects.filter(archived=False).count(), 1)

        resp = bot_api.api_send_complete(target, start_utc, self.RAISE_ON_ERROR, [pk])
        self.assertTrue(resp['ok'])

        # After the "compete" message the new object should still be marked
        # as fresh, but all other objects should be marked as archived.
        self.assertFalse(objects.get(pk=pk).archived)
        self.assertGreater(objects.filter(archived=True).count(), 1)
        self.assertEquals(objects.filter(archived=False).count(), 1)

        # The crawl record should still exist and be marked as "complete".
        self.assertEquals(models.Crawl.objects.count(), 1)
        crawl = models.Crawl.objects.first()
        self.assertEquals(crawl.target, target)
        self.assertEquals(crawl.count, 1)
        self.assertEquals(crawl.status, 'complete')
