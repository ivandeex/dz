from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.conf import settings
import django_tables2 as tables
import django_filters as filters
from . import base
from .views import list_view
from .. import models, helpers


class NewsTable(base.DzTable):

    published = tables.DateTimeColumn(short=False)
    updated = tables.DateTimeColumn(short=False)
    crawled = tables.DateTimeColumn(short=False)

    description = tables.TemplateColumn(
        verbose_name=_('news cut (column)'),
        template_name='dz/tables/news-description.html',
        order_by='newstext__preamble',
    )

    def render_link(self, value):
        return helpers.format_external_link(self.context.request, value)

    def render_archived(self, value):
        return _('Archived') if value else _('Fresh')

    class Meta:
        default = mark_safe('<span class="text-muted">&hellip;</span>')
        model = models.News
        order_by = ('-published', '-id')

        fields = base.DzTable.Meta.fields + (
            'id', 'published', 'sport', 'league',
            'parties', 'title', 'description',
            'updated', 'crawled', 'link', 'archived'
        )


class NewsFilters(filters.FilterSet):
    sport = base.AllValuesCachingFilter()
    league = base.AllValuesCachingFilter()
    archived = base.DzArchivedFilter()

    class Meta:
        model = models.News
        fields = ()


def news_list_view(request):
    return list_view(request, NewsTable, NewsFilters,
                     crawl_target='news')


def newsbox_view(request, pk):
    news = get_object_or_404(models.News, pk=pk)
    context = {
        'news': news,
        'can_follow_links': helpers.user_can_follow(request),
        'link_str': helpers.format_external_link(request, news.link),
    }
    return render(request, 'dz/tables/newsbox-popup.html', context)


def newsbox_img_redirect(request, path):
    '''
    Fix relative url for icons referenced by data table and preamble.
    '''
    new_path = settings.STATIC_URL + settings.WEBPACK_SUBDIR + '/' + path
    return HttpResponsePermanentRedirect(new_path)
