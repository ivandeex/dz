from __future__ import unicode_literals
import logging
import pytz
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db.models import signals
from django.dispatch import receiver
from threading import RLock
from .base import TARGET_CHOICES
from ..config import spider_config

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Schedule(models.Model):
    time = models.TimeField(_('start time (column)'), unique=True)
    target = models.CharField(_('target (column)'), max_length=6, choices=TARGET_CHOICES)

    class Meta:
        verbose_name = _('schedule item (table)')
        verbose_name_plural = _('schedule (table)')

    def __str__(self):
        return u'%s @ %02d:%02d' % (self.target, self.time.hour, self.time.minute)

    _verbose_update = True
    _cache_lock = RLock()
    _cache_date = None
    _cache_schedule = {}  # key: datetime, value: target (or None if fired)

    @classmethod
    def get_next_job(cls, consume):
        with cls._cache_lock:
            now_utc = timezone.now()
            schedule = cls.get_schedule()
            active_utc = list(utc for utc, target in schedule.items() if target[0] != '-')
            if active_utc:
                utc = min(active_utc)
                if utc <= now_utc or not consume:
                    target = schedule[utc]
                    if consume:
                        schedule[utc] = '-' + schedule[utc]
                    return utc, target
        return None, None

    @staticmethod
    def get_local_time():
        now = timezone.now().replace(second=0, microsecond=0)
        schedule_tz = pytz.timezone(spider_config('TIME_ZONE'))
        return now.astimezone(schedule_tz)

    @classmethod
    def get_schedule(cls):
        """Get current schedule"""

        with cls._cache_lock:
            # completely reload schedule at midnight
            this_date = cls.get_local_time().date()

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

            # add only future jobs or jobs within 2 minutes in the past
            now = cls.get_local_time()
            if now.hour == 0 and now.minute <= 2:
                now = now.replace(minute=0)
            else:
                now -= timezone.timedelta(minutes=2)

            # add new jobs to cached schedule
            valid_utc = set()
            for job in cls.objects.all().order_by('time', 'target'):
                time = now.replace(hour=job.time.hour, minute=job.time.minute)
                utc = time.astimezone(timezone.utc)
                if time >= now:
                    # do not replace a job if it's in schedule but already consumed
                    if schedule.get(utc, '.')[0] != '-':
                        schedule[utc] = job.target
                    valid_utc.add(utc)

            # remove deleted jobs from schedule
            for utc in schedule.keys():
                if utc not in valid_utc:
                    del schedule[utc]

        if cls._verbose_update:
            printed_items = ['%02d:%02d->%s' % (utc.hour, utc.minute, target)
                             for utc, target in sorted(schedule.items())]
            logger.info('New schedule (UTC): %s', ', '.join(printed_items))


@receiver(signals.post_save, sender=Schedule)
def on_save_schedule(sender, **kwargs):
    Schedule.update_schedule()


@receiver(signals.post_delete, sender=Schedule)
def on_delete_schedule(sender, **kwargs):
    Schedule.update_schedule()
