from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404
import django_tables2 as tables
from .common import DzTable, list_view
from .. import models, helpers


class TipTable(DzTable):

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
        default = mark_safe('&hellip;')
        model = models.Tip
        order_by = ('-published', '-id')

        fields = (
            'id', 'published', 'league', 'parties', 'description',
            'result', 'tipster', 'odds', 'min_odds',
            'stake', 'earnings', 'spread', 'bookmaker', 'success',
            'updated', 'crawled', 'link', 'archived'
        )


def tip_list_view(request):
    return list_view(request, TipTable, crawl_target='tips')


def tipbox_view(request, pk):
    tip = get_object_or_404(models.Tip, pk=pk)
    ajax_mode = request.is_ajax() or request.GET.get('_ajax')
    template = 'dz/tables/tipbox-popup-%s.html' % ('modal' if ajax_mode else 'page')
    return render(request, template, dict(tip=tip))
