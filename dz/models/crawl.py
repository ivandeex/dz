from __future__ import unicode_literals
import logging
from django.db import models
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from .common import TARGET_CHOICES
from .schedule import Schedule

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Crawl(models.Model):
    # Translators: Job Id
    id = models.AutoField(_('crawl id (column)'), primary_key=True)
    target = models.CharField(_('crawl target (column)'), max_length=6,
                              choices=TARGET_CHOICES, db_index=True)
    manual = models.NullBooleanField(_('crawl type (column)'), db_index=True)
    status = models.CharField(_('crawl status (column)'), max_length=10)
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
        return u'Crawl {} at {}'.format(self.target, self.started)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = 1 + (Crawl.objects.aggregate(Max('id'))['id__max'] or 0)
        super(Crawl, self).save(*args, **kwargs)

    @classmethod
    def add_manual_crawl(cls, target):
        # round time up to next full minute because server-bot api doesn't support seconds
        now_utc = timezone.now().replace(microsecond=0).astimezone(timezone.utc)
        now_utc = (now_utc + timezone.timedelta(seconds=59)).replace(second=0)

        auto_utc, auto_target = Schedule.get_next_job(consume=False)
        if auto_target == target and abs((auto_utc - now_utc).total_seconds()) < 120:
            return 'refused'

        objs = cls.objects
        try:
            objs.get(target=target, status='waiting', manual=True).update(started=now_utc)
            return 'updated'
        except cls.DoesNotExist:
            objs.create(target=target, status='waiting', started=now_utc, manual=True)
            return 'submitted'

    @classmethod
    def get_manual_crawl(cls):
        return cls.objects.filter(status='waiting', manual=True).order_by('id').first()

    @classmethod
    def get_auto_crawl(cls, consume=True):
        utc, target = Schedule.get_next_job(consume)
        if consume and utc and target:
            objs = cls.objects
            crawl = objs.create(target=target, status='waiting', started=utc, manual=False)
            logger.info('Schedule %s crawl at %02d:%02d (UTC)', target, utc.hour, utc.minute)
            return crawl
