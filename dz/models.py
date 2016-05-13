from __future__ import unicode_literals
from django.db import models
from django.utils.html import format_html, strip_tags
from django.utils.encoding import python_2_unicode_compatible
from .utils import as_choices, cut_str


class NewsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(NewsManager, self).get_queryset(*args, **kw)\
            .defer('subtable')\
            #.filter(archived='fresh')


@python_2_unicode_compatible
class News(models.Model):
    id = models.IntegerField('ID', db_column='pk', primary_key=True)
    url = models.URLField('Link')
    title = models.CharField('Title', max_length=150)
    short_title = models.CharField('Participants', max_length=80)
    section = models.CharField('Sport', max_length=20)
    subsection = models.CharField('Liga', max_length=80)
    published = models.DateTimeField('Published')
    updated = models.DateTimeField('Updated')
    crawled = models.DateTimeField('Fetched')
    archived = models.CharField('Archived', max_length=9,
                                choices=as_choices(['archived', 'fresh']))
    preamble = models.CharField(max_length=500, null=True)
    content = models.TextField('Full Content')
    subtable = models.TextField('Subtable')

    def col_content(self):
        return format_html(
            u'<div class="dz_pre">{pre}</div> <div class="dz_body"><span>'
            u'{text}</span> <a href="{url}" target="_blank">(more...)</a></div>',
            pre=cut_str(strip_tags(self.preamble), 60),
            text=cut_str(strip_tags(self.content), 100),
            url='/show_stub?id=%s' % self.id)
    col_content.short_description = 'Content'
    col_content.admin_order_field = 'preamble'


    def __str__(self):
        return u'{} ({})'.format(self.title, self.id)

    objects = NewsManager()

    class Meta:
        verbose_name_plural = 'news'


class TipsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(TipsManager, self).get_queryset(*args, **kw)\
            .defer('text')\
            .filter(archived='fresh')


@python_2_unicode_compatible
class Tip(models.Model):
    id = models.IntegerField('ID', db_column='pk', primary_key=True)
    title = models.CharField('Participants', max_length=150)
    place = models.CharField('Liga', max_length=40)
    tip = models.CharField('Title', max_length=60)
    text = models.TextField('Text', null=True)
    betting = models.CharField('Betting (Kladionica)', max_length=32)
    coeff = models.CharField('Coeff. (Koeficijent)', max_length=6)
    min_coeff = models.CharField('Min Coeff.', max_length=6)
    result = models.CharField('Result (Rezultat)', max_length=15)
    due = models.CharField('Earnings Due (Zarada)', max_length=8)
    spread = models.CharField('Spread (Is. Margina)', max_length=8)
    stake = models.CharField('Stake (Ulog)', max_length=8)
    success = models.CharField(u'Success (Uspje\u0161nost)', max_length=12, null=True)
    tipster = models.CharField('Tipster', max_length=12)
    published = models.DateTimeField('Published (Objavleno)', null=True)
    updated = models.DateTimeField('Updated')
    crawled = models.DateTimeField('Fetched')
    details_url = models.URLField('Link')
    archived = models.CharField(max_length=9, choices=as_choices(['archived', 'fresh']))

    def __str__(self):
        return u'{} ({})'.format(self.tip, self.id)

    objects = TipsManager()

    def col_tip(self):
        return format_html(
            u'<div class="dz_title">{tip}</div>'
            u'<div class="dz_body"><span>{cut}</span> '
            u'<a data-toggle="modal" href="{url}" title="Show text" '
            u'data-target="#fa_modal_window">(more...)</a></div>',
            cut=cut_str(strip_tags(self.text or ''), 80),
            url='show_tip?id=%s' % self.id,
            tip=self.tip)
    col_tip.short_description = 'Tip'
    col_tip.admin_order_field = 'tip'


@python_2_unicode_compatible
class Crawl(models.Model):
    id = models.AutoField('Job Id', primary_key=True)
    type = models.CharField(max_length=8, choices=as_choices(['manual', 'auto']))
    action = models.CharField('Target', max_length=6, choices=as_choices(['news', 'tips']))
    status = models.CharField(max_length=10)
    started = models.DateTimeField('Started At')
    ended = models.DateTimeField('Ended At', null=True)
    news = models.SmallIntegerField('No. Of News')
    tips = models.SmallIntegerField('No. Of Tips')
    host = models.CharField('Hostname', max_length=24)
    ipaddr = models.CharField('IP Address', max_length=20)
    pid = models.CharField('PID', max_length=6)

    def __str__(self):
        return u'Crawl {} at {}'.format(self.action, self.started)


@python_2_unicode_compatible
class User(models.Model):
    username = models.CharField('User Name', max_length=20, unique=True)
    password = models.CharField('Password', max_length=64)
    is_admin = models.BooleanField('Is Administrator')

    def __str__(self):
        return self.username
