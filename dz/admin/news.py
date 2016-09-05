from __future__ import unicode_literals, absolute_import
from django.template.response import TemplateResponse
from django.http import HttpResponseNotFound
from django.conf.urls import url
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .common import DzCrawlModelAdmin, DzExportResource
from .common import DzArchivedListFilter, DzSelectFieldListFilter
from .. import models


class NewsExportResource(DzExportResource):
    class Meta:
        model = models.News
        exclude = ['preamble', 'content', 'subtable']


class NewsAdmin(DzCrawlModelAdmin):
    resource_class = NewsExportResource

    list_display = ['id', 'published', 'sport', 'league',
                    'parties', 'title', 'content_cut',
                    'updated', 'crawled', 'link', 'archived_str']
    if settings.NARROW_GRIDS:
        list_display = ['id', 'published', 'sport', 'league', 'content_cut', 'archived_str']

    list_filter = [('sport', DzSelectFieldListFilter),
                   ('league', DzSelectFieldListFilter),
                   DzArchivedListFilter,
                   'updated',
                   ]

    search_fields = ['parties', 'title', 'preamble', 'content']
    date_hierarchy = 'published'
    exclude = ['content', 'subtable']
    ordering = ['-published', '-id']

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_news')

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_news')

    crawl_action = 'news'

    def content_cut(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/news_content_cut.html',
                               context=dict(news=obj, opts=self.opts))
        return tpl.rendered_content
    content_cut.short_description = _('news cut')
    content_cut.admin_order_field = 'preamble'

    def archived_str(self, obj):
        return _('Archived') if obj.archived else _('Fresh')
    archived_str.short_description = _('archived')
    archived_str.admin_order_field = 'archived'

    def get_urls(self):
        news_content_url = url(
            r'^(?P<id>\d+)/news-content/$',
            self.admin_site.admin_view(self.news_content_view),
            name='%s_%s_news_content' % (self.opts.app_label, self.opts.model_name))
        return [news_content_url] + super(NewsAdmin, self).get_urls()

    def news_content_view(self, request, id):
        news = self.get_object(request, id)
        if news:
            return TemplateResponse(request, 'admin/dz/news_content_popup.html', dict(news=news))
        else:
            return HttpResponseNotFound()
