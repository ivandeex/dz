from __future__ import unicode_literals
import logging
from django.db import models
from django.db.models import Q, Max
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from .base import TARGET_CHOICES
from .schedule import Schedule

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Crawl(models.Model):
    STATUS_CHOICES = [
        ('waiting', _('waiting (crawl status)')),
        ('started', _('started (crawl status)')),
        ('running', _('running (crawl status)')),
        ('complete', _('complete (crawl status)')),
    ]

    CRAWL_TARGETS = ('news', 'tips')

    # Translators: Job Id
    id = models.AutoField(_('crawl id (column)'), primary_key=True)
    target = models.CharField(_('crawl target (column)'), max_length=6,
                              choices=TARGET_CHOICES, db_index=True)
    manual = models.NullBooleanField(_('crawl type (bool column)'), db_index=True)
    status = models.CharField(_('crawl status (column)'), max_length=10,
                              choices=STATUS_CHOICES, db_index=True, null=True)
    started = models.DateTimeField(_('started at (column)'), null=True)
    ended = models.DateTimeField(_('ended at (column)'), null=True)
    count = models.SmallIntegerField(_('no. of items (column)'), default=0)
    host = models.CharField(_('hostname (column)'), max_length=24, db_index=True)
    # Translators: PID
    pid = models.CharField(_('crawler pid (column)'), max_length=6)

    class Meta:
        verbose_name = _('crawl (table)')
        verbose_name_plural = _('crawls (table)')

    def __str__(self):
        start_time = self.started.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%m')
        return u'{} @ {}'.format(self.target, start_time)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = 1 + (Crawl.objects.aggregate(Max('id'))['id__max'] or 0)
        super(Crawl, self).save(*args, **kwargs)

    @staticmethod
    def get_status_message(status):
        # Translators: status from models.Crawl is one of: refused, updated, submitted
        return _('Crawling %s!' % status)
        if None:
            _('Crawling refused!')
            _('Crawling updated!')
            _('Crawling submitted!')

    @classmethod
    def add_manual_crawl(cls, target):
        if target not in cls.CRAWL_TARGETS:
            return 'refused'

        # round time up to next full minute because server-bot api doesn't support seconds
        now_utc = timezone.now().replace(microsecond=0).astimezone(timezone.utc)
        now_utc = (now_utc + timezone.timedelta(seconds=59)).replace(second=0)

        # check that auto job with same time does not exist
        auto_utc, auto_target = Schedule.get_next_job(consume=False)
        if auto_target == target and abs((auto_utc - now_utc).total_seconds()) <= 120:
            return 'refused'

        # shift for later time if there is an active manual job with same time
        while cls.objects.filter(started=now_utc).filter(~Q(status='waiting')).exists():
            now_utc += timezone.timedelta(minutes=1)

        # update time of existing waiting job or create a new job
        try:
            wjob = cls.objects.get(target=target, status='waiting', manual=True)
            wjob.started = now_utc
            wjob.save()
            return 'updated'
        except cls.DoesNotExist:
            cls.objects.create(target=target, status='waiting', started=now_utc, manual=True)
            return 'submitted'

    @classmethod
    def get_manual_crawl(cls):
        return cls.objects.filter(status='waiting', manual=True).order_by('id').first()

    @classmethod
    def get_auto_crawl(cls):
        utc, target = Schedule.get_next_job(consume=True)
        if not utc:
            return
        if cls.objects.filter(target=target, started=utc, manual=False).exists():
            logger.info('Auto-skip %s crawl at %02d:%02d (UTC)', target, utc.hour, utc.minute)
            return
        logger.info('Schedule %s crawl at %02d:%02d (UTC)', target, utc.hour, utc.minute)
        return cls.objects.create(target=target, status='waiting', started=utc, manual=False)

    @classmethod
    def from_json(cls, req):
        from ..api import api2time

        running_crawls = cls.objects.filter(status__in=['started', 'running'])
        crawl, created = running_crawls.get_or_create(
            started=api2time(req['start_utc'], 'UTC'),
            target=req['target'],
            host=req['host'],
            pid=req['pid'],
        )
        return crawl
