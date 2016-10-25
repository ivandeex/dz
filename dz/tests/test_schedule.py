import pytz
from mock import patch
from django.test import tag
from django.utils import timezone
from django.conf import settings
from dz.models import Schedule
from . import base


@tag('schedule')
class ScheduleTests(base.BaseDzTestCase):
    def get_schedule_jobs(self):
        jobs = []
        while True:
            utc, target = Schedule.get_next_job(consume=True)
            if utc:
                jobs.append((utc, target))
            else:
                break
        return jobs

    @Schedule.suspend_logging
    def test_schedule_should_update_overnight(self):
        # save initial value
        real_now = timezone.now()

        # calculate times of schedule switching
        local_tz = pytz.timezone(settings.TIME_ZONE)
        local_now = real_now.astimezone(local_tz)
        local_midnight = local_now.replace(hour=0, minute=0, second=1, microsecond=0)
        local_midnight_utc = local_midnight.astimezone(timezone.utc)

        with patch('django.utils.timezone.now') as fake_now:
            # jump time to the next day *start*
            fake_now.return_value = local_midnight_utc + timezone.timedelta(days=1)

            # the schedule gets recalculated, but jobs are not active yet
            jobs1 = self.get_schedule_jobs()
            self.assertEquals(len(jobs1), 0)

            # jump time to the next day *end*
            fake_now.return_value = local_midnight_utc + timezone.timedelta(days=1, hours=23)

            # jobs are active and ready for consumption
            jobs2 = self.get_schedule_jobs()
            self.assertEquals(len(jobs2), base.SCHEDULE_FIXTURE_LENGTH)

            # jobs are already consumed
            jobs3 = self.get_schedule_jobs()
            self.assertEquals(len(jobs3), 0)
