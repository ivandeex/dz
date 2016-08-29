from __future__ import unicode_literals, absolute_import
from django.contrib import admin
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

    list_display = ['id', 'published', 'section', 'subsection',
                    'short_title', 'title', 'col_content',
                    'updated', 'crawled', 'url', 'archived']
    if settings.NARROW_GRIDS:
        list_display = ['id', 'published', 'section', 'subsection',
                        'col_content', 'archived']
    list_filter = [('section', DzSelectFieldListFilter),
                   ('subsection', DzSelectFieldListFilter),
                   DzArchivedListFilter,
                   'updated',
                   ]
    search_fields = ['short_title', 'title', 'preamble', 'content']
    date_hierarchy = 'published'
    exclude = ['content', 'subtable']
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_news')

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_news')

    def col_content(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/news_content_col.html',
                               context=dict(obj=obj, opts=self.opts))
        return tpl.rendered_content
    col_content.short_description = _('short news content')
    col_content.admin_order_field = 'preamble'

    def get_urls(self):
        news_stub_url = url(r'^(?P<id>\d+)/news_stub/$',
                            self.admin_site.admin_view(self.news_stub_view),
                            name='%s_%s_news_stub' % (self.opts.app_label, self.opts.model_name))
        return [news_stub_url] + super(NewsAdmin, self).get_urls()

    def news_stub_view(self, request, id):
        obj = self.get_object(request, id)
        if obj:
            return TemplateResponse(request, 'admin/dz/news_stub.html', dict(obj=obj))
        else:
            return HttpResponseNotFound()
