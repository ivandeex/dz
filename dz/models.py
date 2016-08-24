from __future__ import unicode_literals
from django.db import models
from django.utils.html import format_html, strip_tags
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from .utils import cut_str
from .auth import User  # noqa


ARCHIVED_CHOICES = [
    ('archived', _('Archived')),
    ('fresh', _('Fresh')),
]


class NewsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(NewsManager, self).get_queryset(*args, **kw).defer('subtable')


@python_2_unicode_compatible
class News(models.Model):
    id = models.IntegerField(_('news id'), db_column='pk', primary_key=True)
    url = models.URLField(_('news link'))
    title = models.CharField(_('news title'), max_length=150)
    short_title = models.CharField(_('participants'), max_length=80)
    section = models.CharField(_('sport'), max_length=20)
    subsection = models.CharField(_('liga'), max_length=80)
    published = models.DateTimeField(_('published'))
    updated = models.DateTimeField(_('updated'))
    crawled = models.DateTimeField(_('fetched'))
    archived = models.CharField(_('archived'), max_length=9, choices=ARCHIVED_CHOICES)
    preamble = models.CharField(_('news preamble'), max_length=500, null=True)
    content = models.TextField(_('full news content'))
    subtable = models.TextField(_('news subtable'))

    def col_content(self):
        return format_html(
            u'<div class="dz_pre">{pre}</div> <div class="dz_body"><span>'
            u'{text}</span> <a href="{url}" target="_blank">(more...)</a></div>',
            pre=cut_str(strip_tags(self.preamble), 60),
            text=cut_str(strip_tags(self.content), 100),
            url='/show_stub?id=%s' % self.id)
    col_content.short_description = _('short news content')
    col_content.admin_order_field = 'preamble'

    def __str__(self):
        return u'{} ({})'.format(self.title, self.id)

    objects = NewsManager()

    class Meta:
        verbose_name = _('news')
        verbose_name_plural = _('newss')
        index_together = [
            ['published', 'archived']
        ]
        permissions = [
            ('crawl_news', _('Can crawl news')),
            ('view_news', _('Can only view news')),
        ]


class TipsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kw):
        return super(TipsManager, self).get_queryset(*args, **kw).defer('text')


@python_2_unicode_compatible
class Tip(models.Model):
    id = models.IntegerField(_('tip id'), db_column='pk', primary_key=True)
    title = models.CharField(_('participants'), max_length=150, db_index=True)
    place = models.CharField(_('liga'), max_length=40, db_index=True)
    tip = models.CharField(_('tip title'), max_length=60)
    text = models.TextField('tip text', null=True)
    # Translators: Betting (Kladionica)
    betting = models.CharField(_('betting'), max_length=32)
    # Translators: Coeff. (Koeficijent)
    coeff = models.CharField(_('tip coefficient'), max_length=6)
    min_coeff = models.CharField(_('minimum tip coeff'), max_length=6)
    # Translators: Result (Rezultat)
    result = models.CharField(_('tip result'), max_length=15)
    # Translators: Earnings Due (Zarada)
    due = models.CharField(_('earnings'), max_length=8)
    # Translators: Spread (Is. Margina)
    spread = models.CharField(_('spread'), max_length=8)
    # Translators: Stake (Ulog)
    stake = models.CharField(_('stake'), max_length=8)
    # Translators: Success (Uspje\u0161nost)
    success = models.CharField(_('tip success'), max_length=12, null=True)
    tipster = models.CharField(_('tipster'), max_length=12)
    # Translators: Published (Objavleno)
    published = models.DateTimeField(_('published'), null=True, db_index=True)
    updated = models.DateTimeField(_('updated'))
    crawled = models.DateTimeField(_('fetched'))
    details_url = models.URLField(_('tip link'))
    archived = models.CharField(_('archived'), max_length=9, choices=ARCHIVED_CHOICES)

    def col_tip(self):
        return format_html(
            u'<div class="dz_title">{tip}</div>'
            u'<div class="dz_body"><span>{cut}</span> '
            u'<a data-toggle="modal" href="{url}" title="Show text" '
            u'data-target="#fa_modal_window">(more...)</a></div>',
            cut=cut_str(strip_tags(self.text or ''), 80),
            url='show_tip?id=%s' % self.id,
            tip=self.tip)
    col_tip.short_description = _('short tip')
    col_tip.admin_order_field = 'tip'

    def __str__(self):
        return u'{} ({})'.format(self.tip, self.id)

    objects = TipsManager()

    class Meta:
        verbose_name = _('tip')
        verbose_name_plural = _('tips')
        index_together = [
            ['published', 'archived']
        ]
        permissions = [
            ('crawl_tips', _('Can crawl tips')),
            ('view_tips', _('Can only view tips')),
        ]


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
    type = models.CharField(_('crawl type'), max_length=8, choices=TYPE_CHOICES)
    action = models.CharField(_('crawl target'), max_length=6, choices=ACTION_CHOICES)
    status = models.CharField(_('crawl status'), max_length=10)
    started = models.DateTimeField(_('started at'))
    ended = models.DateTimeField(_('ended at'), null=True)
    news = models.SmallIntegerField(_('no. of news'))
    tips = models.SmallIntegerField(_('no. of tips'))
    host = models.CharField(_('hostname'), max_length=24)
    ipaddr = models.CharField(_('ip address'), max_length=20)
    # Translators: PID
    pid = models.CharField(_('crawler pid'), max_length=6)

    def __str__(self):
        return u'Crawl {} at {}'.format(self.action, self.started)

    class Meta:
        verbose_name = _('crawl')
        verbose_name_plural = _('crawls')
