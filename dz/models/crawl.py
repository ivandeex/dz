from __future__ import unicode_literals
import logging
from django.db import models
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from .common import TYPE_CHOICES, ACTION_CHOICES
from .schedule import Schedule

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Crawl(models.Model):
    # Translators: Job Id
    id = models.AutoField(_('crawl id'), primary_key=True)
    type = models.CharField(_('crawl type'), max_length=8,
                            choices=TYPE_CHOICES, db_index=True)
    action = models.CharField(_('crawl target'), max_length=6,
                              choices=ACTION_CHOICES, db_index=True)
    status = models.CharField(_('crawl status'), max_length=10)
    started = models.DateTimeField(_('started at'), null=True)
    ended = models.DateTimeField(_('ended at'), null=True)
    count = models.SmallIntegerField(_('no. of items'), default=0)
    host = models.CharField(_('hostname'), max_length=24, db_index=True)
    # Translators: PID
    pid = models.CharField(_('crawler pid'), max_length=6)

    class Meta:
        verbose_name = _('crawl')
        verbose_name_plural = _('crawls')

    def __str__(self):
        return u'Crawl {} at {}'.format(self.action, self.started)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = 1 + (Crawl.objects.aggregate(Max('id'))['id__max'] or 0)
        super(Crawl, self).save(*args, **kwargs)

    @classmethod
    def add_manual_crawl(cls, action):
        now = timezone.now().replace(microsecond=0)
        auto_time, auto_action = Schedule.get_next_job(consume=False)
        if auto_action == action and abs((auto_time - now).total_seconds()) < 60:
            return 'refused'
        try:
            Crawl.objects.get(action=action, status='waiting').update(started=now)
            return 'updated'
        except Crawl.DoesNotExist:
            Crawl.objects.create(action=action, status='waiting', started=now, type='manual')
            return 'added'

    @classmethod
    def get_manual_crawl(cls):
        return cls.objects.filter(status='waiting').order_by('pk').first()

    @classmethod
    def get_auto_crawl(cls, consume=True):
        time, action = Schedule.get_next_job(consume)
        if consume and time and action:
            logger.info('Schedule auto job %s at %02d:%02d', action, time.hour, time.minute)
            crawl = cls.objects.create(action=action, status='waiting', started=time, type='auto')
            return crawl
