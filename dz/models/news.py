from __future__ import unicode_literals
import re
from django.db import models
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

    # large text fields
    preamble = models.CharField(_('news preamble (column)'), max_length=500, null=True)
    content = models.TextField(_('full news content (column)'))
    subtable = models.TextField(_('news subtable (column)'))

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

    class Manager(models.Manager):
        use_for_related_fields = True

        def get_queryset(self, *args, **kw):
            qs = super(News.Manager, self).get_queryset(*args, **kw)
            # Defer large text fields content and preamble, replace with cuts by default
            qs = qs.defer('content').annotate(content_cut=CutStr('content', 100))
            qs = qs.defer('preamble').annotate(preamble_cut=CutStr('preamble', 60))
            return qs

    objects = Manager()

    def __str__(self):
        return u'{} ({})'.format(self.title, self.id)

    @classmethod
    def get_seen_ids(cls):
        return cls.objects.distinct('id').order_by('id').values_list('id', flat=True)

    def save(self, *args, **kwargs):
        # Do not let user click on external links in content or data table.
        def deactivate_links(html):
            return re.sub(r'(<a|&lt;a)\s([^>]*?)\bhref="([^#][^"]+)"(.*?)>',
                          r'\1 \2href="##\3"\4>', html)
        self.content = deactivate_links(self.content)
        self.subtable = deactivate_links(self.subtable)
        return super(News, self).save(*args, **kwargs)
