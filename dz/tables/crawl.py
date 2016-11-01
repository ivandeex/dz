from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from .base import DzTable
from .views import list_view
from .. import models


class CrawlTable(DzTable):
    type_str = tables.Column(
        verbose_name=_('crawl type (str column)'),
        empty_values=(),
        accessor='manual',
    )

    started = tables.DateTimeColumn(short=False)
    ended = tables.DateTimeColumn(short=False)

    def render_type_str(self, value):
        if value is None:
            return _('orphan (crawl type)')
        elif value:
            return _('manual (crawl type)')
        else:
            return _('scheduled (crawl type)')

    class Meta:
        model = models.Crawl
        order_by = '-id'

        fields = DzTable.Meta.fields + (
            'id', 'target', 'type_str', 'status',
            'started', 'ended', 'count', 'host', 'pid'
        )


def crawl_list_view(request):
    return list_view(request, CrawlTable, None,
                     restricted=True)
