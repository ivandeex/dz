import pytz
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

MODEL_BATCH_SIZE = 20
SCHEDULE_FIXTURE_LENGTH = 5


def get_pass(username):
    return '%s.pass' % username


class BaseDzTestsMixin(object):
    fixtures = ['schedule.json']

    # suspend schedule logging while fixtures are loaded
    @classmethod
    @models.Schedule.suspend_logging
    def setUpClass(cls):
        super(BaseDzTestsMixin, cls).setUpClass()

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
