import pytz
from datetime import time
from contextlib import contextmanager
from django.utils import timezone
from django.conf import settings
from django.test import TestCase, override_settings
from dz import models
from . import factories


TEST_USERS = [
    dict(name='admin', admin=True, follow=True),
    dict(name='super', admin=True, follow=False),
    dict(name='follow', admin=True, follow=True),
    dict(name='simple', admin=False, follow=False),
]

TEST_SCHEDULE = [
    (time(11, 02), 'tips'),
    (time(11, 46), 'tips'),
    (time(12, 02), 'tips'),
    (time(10, 00), 'news'),
    (time(18, 30), 'news'),
]

MODEL_BATCH_SIZE = 20


def get_pass(username):
    return '%s.pass' % username


class BaseDzTestsMixin(object):
    # prepare database for unit tests
    def setUp(self):
        server_tz = pytz.timezone(settings.TIME_ZONE)
        now_aware = timezone.now().astimezone(server_tz)
        self.cur_tz_name = now_aware.strftime('%Z')

        for user in TEST_USERS:
            models.User.objects.create(
                username=user['name'], password=get_pass(user['name']),
                is_admin=user['admin'], can_follow=user['follow']
            )

        models.Schedule._verbose_update = False
        for time_i, target_i in TEST_SCHEDULE:
            models.Schedule.objects.create(time=time_i, target=target_i)
        models.Schedule._verbose_update = False

        factories.CrawlFactory.create_batch(MODEL_BATCH_SIZE)
        factories.TipFactory.create_batch(MODEL_BATCH_SIZE)

        # Linked NewsText objects will be created automatically.
        factories.NewsFactory.create_batch(MODEL_BATCH_SIZE)

    @contextmanager
    def login_as(self, username):
        self.client.login(username=username, password=get_pass(username))
        yield
        self.client.logout()


@override_settings(TESTING=True)
class BaseDzTestCase(BaseDzTestsMixin, TestCase):
    pass
