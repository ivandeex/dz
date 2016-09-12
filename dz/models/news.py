from __future__ import unicode_literals
import re
from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from .common import CutStr


@python_2_unicode_compatible
class News(models.Model):

    id = models.IntegerField(_('news id (column)'), db_column='pk', primary_key=True)
    link = models.URLField(_('news link (column)'))
    title = models.CharField(_('news title (column)'), max_length=150)
    sport = models.CharField(_('sport (column)'), max_length=20, db_index=True)
    league = models.CharField(_('league (column)'), max_length=80, db_index=True)
    parties = models.CharField(_('parties (column)'), max_length=80)
    published = models.DateTimeField(_('published (column)'))
    updated = models.DateTimeField(_('updated (column)'), db_index=True)
    crawled = models.DateTimeField(_('fetched (column)'))
    archived = models.BooleanField(_('archived (column)'))

    class Meta:
        verbose_name = _('news (table)')
        verbose_name_plural = _('many news (table)')
        index_together = [
            ['published', 'archived']
        ]
        permissions = [
            ('crawl_news', _('Can crawl news')),
            ('view_news', _('Can only view news')),
            ('follow_news', _('Can click on news links')),
        ]

    def __str__(self):
        return u'{} ({})'.format(self.title, self.id)

    @classmethod
    def get_seen_ids(cls):
        return cls.objects.distinct('id').order_by('id').values_list('id', flat=True)

    def _get_newstext_cuts(self):
        if getattr(self, '_newstext_cuts', None) is None:
            self._newstext_cuts = (
                NewsText.objects.filter(pk=self.pk)
                .annotate(content_cut=CutStr('content', settings.FIELD_CUT_LENGTH))
                .annotate(preamble_cut=CutStr('preamble', settings.FIELD_CUT_LENGTH))
                .values('content_cut', 'preamble_cut')
                .order_by()  # reset all orderings, but first() will force ordering by id
                .first()
            ) or {'content_cut': '', 'preamble_cut': ''}
        return self._newstext_cuts

    @property
    def content_cut(self):
        return self._get_newstext_cuts()['content_cut']

    @property
    def preamble_cut(self):
        return self._get_newstext_cuts()['preamble_cut']

    @staticmethod
    def from_json(data):
        pk = int(data['id'])
        try:
            news = News.objects.get(pk=pk)
        except News.DoesNotExist:
            news = News(pk=pk)
        try:
            news.newstext
        except NewsText.DoesNotExist:
            news.newstext = NewsText(pk=pk)

        for field, value in data.items():
            if field.startswith('newstext.'):
                setattr(news.newstext, field.split('.')[1], value)
            else:
                setattr(news, field, value)

        news.save()
        news.newstext.save()
        return news

    def save(self, *args, **kwargs):
        # remove comma part from league strings
        self.league = self.league.partition(',')[0]

        super(News, self).save(*args, **kwargs)


class NewsText(models.Model):

    news = models.OneToOneField(News, on_delete=models.CASCADE, primary_key=True)

    # large text fields
    preamble = models.CharField(_('news preamble (column)'), max_length=500, null=True)
    content = models.TextField(_('full news content (column)'))
    datatable = models.TextField(_('news datatable (column)'))

    def save(self, *args, **kwargs):

        # do not let user click on external links in content or data table
        def deactivate_links(html):
            return re.sub(r'(<a|&lt;a)\s([^>]*?)\bhref="([^#][^"]+)"(.*?)>',
                          r'\1 \2href="##\3"\4>',
                          html)

        def fix_bookmaker_img(html):
            return re.sub(r'<img\s([^>]*?)\bsrc="img/kladionice/([^/"]+)"(.*?)>',
                          r'<img \1src="img/bookmaker-\2"\3>',
                          html)

        # deactivate external links in content and data
        self.content = deactivate_links(self.content)
        self.datatable = deactivate_links(self.datatable)

        # correct path of bookmaker images
        self.datatable = fix_bookmaker_img(self.datatable)

        super(NewsText, self).save(*args, **kwargs)
