from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class Crawl(models.Model):
    TYPE_CHOICES = [
        ('manual', _('manual crawl')),
        ('auto', _('auto crawl')),
    ]

    ACTION_CHOICES = [
        ('news', _('news crawl')),
        ('tips', _('tips crawl')),
    ]

    # Translators: Job Id
    id = models.AutoField(_('crawl id'), primary_key=True)
    type = models.CharField(_('crawl type'), max_length=8,
                            choices=TYPE_CHOICES, db_index=True)
    action = models.CharField(_('crawl target'), max_length=6,
                              choices=ACTION_CHOICES, db_index=True)
    status = models.CharField(_('crawl status'), max_length=10)
    started = models.DateTimeField(_('started at'))
    ended = models.DateTimeField(_('ended at'), null=True)
    news = models.SmallIntegerField(_('no. of news'))
    tips = models.SmallIntegerField(_('no. of tips'))
    host = models.CharField(_('hostname'), max_length=24, db_index=True)
    ipaddr = models.CharField(_('ip address'), max_length=20)
    # Translators: PID
    pid = models.CharField(_('crawler pid'), max_length=6)

    def __str__(self):
        return u'Crawl {} at {}'.format(self.action, self.started)

    class Meta:
        verbose_name = _('crawl')
        verbose_name_plural = _('crawls')
