from __future__ import unicode_literals
from django.db import models


ARCHIVED_CHOICES = [
    ('archived', 'archived'),
    ('fresh', 'fresh'),
]


class User(models.Model):
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=64)
    is_admin = models.BooleanField()

    def __unicode__(self):
        return self.username


class NewsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(NewsManager, self).get_queryset(*args, **kw)\
            .defer('content', 'subtable', 'preamble')


class News(models.Model):
    pkey = models.IntegerField(db_column='pk', primary_key=True)
    url = models.URLField()
    title = models.CharField(max_length=150)
    short_title = models.CharField(max_length=80)
    section = models.CharField(max_length=20)
    subsection = models.CharField(max_length=80)
    published = models.DateTimeField()
    updated = models.DateTimeField()
    crawled = models.DateTimeField()
    archived = models.CharField(max_length=9, choices=ARCHIVED_CHOICES)
    preamble = models.CharField(max_length=500, null=True)
    content = models.TextField()
    subtable = models.TextField()

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.pkey)

    objects = NewsManager()

    class Meta:
        verbose_name_plural = 'news'


class TipsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(TipsManager, self).get_queryset(*args, **kw).defer('text')


class Tip(models.Model):
    pkey = models.IntegerField(db_column='pk', primary_key=True)
    title = models.CharField(max_length=150)
    place = models.CharField(max_length=40)
    tip = models.CharField(max_length=60)
    text = models.TextField(null=True)
    betting = models.CharField(max_length=32)
    coeff = models.CharField(max_length=6)
    min_coeff = models.CharField(max_length=6)
    result = models.CharField(max_length=15)
    due = models.CharField(max_length=8)
    spread = models.CharField(max_length=8)
    stake = models.CharField(max_length=8)
    success = models.CharField(max_length=12, null=True)
    tipster = models.CharField(max_length=12)
    published = models.DateTimeField(null=True)
    updated = models.DateTimeField()
    crawled = models.DateTimeField()
    details_url = models.URLField()
    archived = models.CharField(max_length=9, choices=ARCHIVED_CHOICES)

    def __unicode__(self):
        return u'{} ({})'.format(self.tip, self.pkey)

    objects = TipsManager()


class Crawl(models.Model):
    type = models.CharField(max_length=8)
    action = models.CharField(max_length=6)
    status = models.CharField(max_length=10)
    started = models.DateTimeField()
    ended = models.DateTimeField(null=True)
    news = models.SmallIntegerField()
    tips = models.SmallIntegerField()
    host = models.CharField(max_length=24)
    ipaddr = models.CharField(max_length=20)
    pid = models.CharField(max_length=6)

    def __unicode__(self):
        return u'Crawl {} at {}'.format(self.action, self.started)
