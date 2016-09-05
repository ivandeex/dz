from __future__ import unicode_literals
import logging
import pytz
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from threading import RLock
from datetime import timedelta
from .common import TARGET_CHOICES

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Schedule(models.Model):
    # Default_schedule:
    # time(11, 02): 'tips'
    # time(11, 46): 'tips'
    # time(12, 02): 'tips'
    # time(10, 00): 'news'
    # time(18, 30): 'news'

    time = models.TimeField(_('start time'))
    target = models.CharField(_('target'), max_length=6, choices=TARGET_CHOICES)

    class Meta:
        verbose_name = _('job')
        verbose_name_plural = _('schedule')

    def __str__(self):
        return u'Schedule %s at %02d:%02d' % (self.target, self.time.hour, self.time.minute)

    _cache_lock = RLock()
    _cache_date = None
    _cache_schedule = {}  # key: datetime, value: target (or None if fired)

    @classmethod
    def get_next_job(cls, consume):
        with cls._cache_lock:
            schedule = cls.get_schedule()
            active_times = list(time for time, target in schedule.items() if target[0] != '-')
            if active_times:
                time = min(active_times)
                if time <= timezone.now() or not consume:
                    target = schedule[time]
                    if consume:
                        schedule[time] = '-' + schedule[time]
                    return time, target
        return None, None

    @classmethod
    def get_schedule(cls):
        """Get current schedule"""

        with cls._cache_lock:
            # completely reload schedule at midnight
            schedule_tz = pytz.timezone(settings.SPIDER_TIME_ZONE)
            this_date = timezone.now().astimezone(schedule_tz).date()
            if cls._cache_date != this_date:
                cls._cache_date = this_date
                cls._cache_schedule = {}
                cls.update_schedule()
            return cls._cache_schedule

    @classmethod
    def update_schedule(cls):
        """Update schedule after database changes or at midnight"""

        with cls._cache_lock:
            schedule = cls._cache_schedule
            valid_times = set()

            # add only future jobs or jobs within 5 minutes in the past
            schedule_tz = pytz.timezone(settings.SPIDER_TIME_ZONE)
            now = timezone.now().astimezone(schedule_tz).replace(second=0, microsecond=0)
            if now.hour == 0 and now.minute <= 5:
                now = now.replace(minute=0)
            else:
                now -= timedelta(minutes=5)

            # add new jobs to cached schedule
            for job in cls.objects.all().order_by('time', 'target'):
                time = now.replace(hour=job.time.hour, minute=job.time.minute)
                if time >= now:
                    valid_times.add(time)
                    if time not in schedule:
                        schedule[time] = job.target

            # remove deleted jobs from schedule
            for time in schedule.keys():
                if time not in valid_times:
                    del schedule[time]

        printed_items = ['%02d:%02d->%s' % (time.hour, time.minute, target)
                         for time, target in sorted(schedule.items())]
        logger.info('New schedule: %s', ', '.join(printed_items))


@receiver(signals.post_save, sender=Schedule)
def on_save_schedule(sender, **kwargs):
    Schedule.update_schedule()


@receiver(signals.post_delete, sender=Schedule)
def on_delete_schedule(sender, **kwargs):
    Schedule.update_schedule()
