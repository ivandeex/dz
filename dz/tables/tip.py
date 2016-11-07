from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404
import django_tables2 as tables
import django_filters as filters
from . import base
from .views import list_view
from .utils import lazy_i18n_title
from .. import models, helpers


class TipTable(base.DzTable):

    published = tables.DateTimeColumn(short=False)
    updated = tables.DateTimeColumn(short=False)
    crawled = tables.DateTimeColumn(short=False)

    description = tables.TemplateColumn(
        verbose_name=_('tip cut (column)'),
        template_name='dz/tables/tip-description.html',
        order_by='title',
    )

    SUCCESS_CODE_MAP = {
        'unknown': _('(success) unknown'),
        'hit': _('(success) hit'),
        'miss': _('(success) miss'),
    }

    def render_success(self, value):
        return self.SUCCESS_CODE_MAP.get(value, value)

    def render_link(self, value):
        return helpers.format_external_link(self.context.request, value)

    def render_archived(self, value):
        return _('Archived') if value else _('Fresh')

    class Meta:
        default = mark_safe('<span class="text-muted">&hellip;</span>')
        model = models.Tip
        order_by = ('-published', '-id')

        fields = base.DzTable.Meta.fields + (
            'id', 'published', 'league', 'parties', 'description',
            'result', 'tipster', 'odds', 'min_odds',
            'stake', 'earnings', 'spread', 'bookmaker', 'success',
            'updated', 'crawled', 'link', 'archived'
        )


class TipFilters(base.FilterSetWithSearch):

    search = filters.CharFilter(
        label=lazy_i18n_title('search'),
        method='filter_search',
        name='parties title text',
    )

    archived = base.DzArchivedFilter(label=lazy_i18n_title('archived (column)'))
    tipster = base.AllValuesCachingFilter(label=lazy_i18n_title('tipster (column)'))
    league = base.AllValuesCachingFilter(label=lazy_i18n_title('tip league (column)'))
    parties = base.AllValuesCachingFilter(label=lazy_i18n_title('tip parties (column)'))

    class Meta:
        model = models.Tip
        fields = ()


def tip_list_view(request):
    return list_view(request, TipTable, TipFilters,
                     crawl_target='tips')


def tipbox_view(request, pk):
    tip = get_object_or_404(models.Tip, pk=pk)
    ajax_mode = request.is_ajax() or request.GET.get('_ajax')
    template = 'dz/tables/tipbox-popup-%s.html' % ('modal' if ajax_mode else 'page')
    return render(request, template, dict(tip=tip))
