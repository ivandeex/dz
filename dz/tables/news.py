from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django import forms
import django_tables2 as tables
import django_filters as filters
from . import base
from .views import list_view
from .export import export_view
from .utils import lazy_i18n_title
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

    def render_id(self, value):
        context = self.context
        if self.is_admin or 'form_url' not in context:
            return value
        form_url = reverse(context['form_url'], kwargs={'pk': value})
        if context['preserved_query']:
            form_url += '?' + context['preserved_query']
        return mark_safe('<a href="{}">{}</a>'.format(form_url, value))

    def render_link(self, value):
        return helpers.format_external_link(self.context.request, value)

    def render_archived(self, value):
        return _('Archived') if value else _('Fresh')

    class Meta:
        per_page = 50
        default = mark_safe('<span class="text-muted">&hellip;</span>')
        model = models.News
        order_by = ('-published', '-id')

        fields = base.DzTable.Meta.fields + (
            'id', 'published', 'sport', 'league',
            'parties', 'title', 'description',
            'updated', 'crawled', 'link', 'archived'
        )


class NewsFilters(base.FilterSetWithSearch):

    search = filters.CharFilter(
        label=lazy_i18n_title('Search'),
        method='filter_search',
        name='parties title newstext__preamble newstext__content',
    )

    sport = base.AllValuesCachingFilter(label=lazy_i18n_title('sport (column)'))
    league = base.AllValuesCachingFilter(label=lazy_i18n_title('league (column)'))
    archived = base.DzArchivedFilter(label=lazy_i18n_title('archived (column)'))
    updated = filters.DateRangeFilter(label=lazy_i18n_title('updated (column)'))

    class Meta:
        model = models.News
        fields = ()


class NewsForm(forms.ModelForm):
    class Meta:
        model = models.News
        fields = '__all__'


def news_list_view(request):
    return list_view(request, NewsTable, NewsFilters, 'news-form',
                     export_url='news-export', crawl_target='news')


def news_export_view(request):
    return export_view(request, NewsTable, NewsFilters)


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
