from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
import django_filters as filters
from . import base
from .views import list_view
from .utils import lazy_i18n_title
from ..models.base import TARGET_CHOICES
from .. import models


class CrawlTable(base.DzTable):
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

        fields = base.DzTable.Meta.fields + (
            'id', 'target', 'type_str', 'status',
            'started', 'ended', 'count', 'host', 'pid'
        )


class CrawlFilters(filters.FilterSet):
    ALL_CHOICE = [(None, _('All'))]
    STATUS_CHOICES = ALL_CHOICE + models.Crawl.STATUS_CHOICES
    TYPE_CHOICES = ALL_CHOICE + [
        ('-', _('orphan (crawl type)')),
        (False, _('scheduled (crawl type)')),
        (True, _('manual (crawl type)')),
    ]

    target = filters.ChoiceFilter(
        label=lazy_i18n_title('crawl target (column)'),
        choices=ALL_CHOICE + TARGET_CHOICES,
    )

    status = filters.ChoiceFilter(
        label=lazy_i18n_title('crawl status (column)'),
        choices=STATUS_CHOICES,
    )

    manual = filters.ChoiceFilter(
        label=lazy_i18n_title('crawl type (bool column)'),
        choices=TYPE_CHOICES,
        method='filter_manual',
    )

    def filter_manual(self, queryset, name, value):
        if value is None:
            return queryset
        elif value == '-':
            return queryset.filter(**{name + '__isnull': True})
        else:
            return queryset.filter(**{name: value})

    class Meta:
        model = models.Crawl
        fields = ()

def crawl_list_view(request):
    return list_view(request, CrawlTable, CrawlFilters,
                     restricted=True)
