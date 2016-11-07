from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404
import django_tables2 as tables
import django_filters as filters
from . import base
from .views import list_view
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


class TipFilters(filters.FilterSet):
    archived = base.DzArchivedFilter()
    tipster = base.AllValuesCachingFilter()
    league = base.AllValuesCachingFilter()
    parties = base.AllValuesCachingFilter()

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
