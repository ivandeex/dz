from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
import django_tables2 as tables
from .common import DzTable, list_view
from .. import models


class NewsTable(DzTable):

    published = tables.DateTimeColumn(short=False)
    updated = tables.DateTimeColumn(short=False)
    crawled = tables.DateTimeColumn(short=False)

    description = tables.TemplateColumn(
        verbose_name=_('news cut (column)'),
        template_name='dz/tables/news-description.html',
        order_by='newstext__preamble',
    )

    def render_link(self, value):
        return self.format_external_link(value)

    def render_archived(self, value):
        return _('Archived') if value else _('Fresh')

    class Meta:
        default = mark_safe('&hellip;')
        model = models.News
        order_by = ('-published', '-id')

        fields = (
            'id', 'published', 'sport', 'league',
            'parties', 'title', 'description',
            'updated', 'crawled', 'link', 'archived'
        )


def news_list_view(request):
    return list_view(request, NewsTable)
