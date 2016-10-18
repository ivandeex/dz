from django.test import LiveServerTestCase, tag, override_settings
from django.conf import settings
from dz import models
from . import base


@tag('liveserver')
@override_settings(TESTING=True)
class DzLiveServerTest(base.BaseDzTestsMixin, LiveServerTestCase):
    # suspend schedule logging while fixtures are loaded
    @models.Schedule.suspend_logging
    def _fixture_setup(self):
        super(DzLiveServerTest, self)._fixture_setup()

    @models.Schedule.suspend_logging
    def test_liveserver(self):
        if settings.TEST_LIVESERVER:
            # use newline to force prompt printing in honcho
            raw_input('Hit Enter to end liveserver...\n')
