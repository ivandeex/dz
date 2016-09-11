from __future__ import unicode_literals, absolute_import
import re
from django.template.response import TemplateResponse
from django.http.response import HttpResponseNotFound, HttpResponsePermanentRedirect
from django.conf.urls import url
from django.conf import settings
from django.utils.html import format_html
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
                    'updated', 'crawled', 'link_str', 'archived_str']
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

    def user_can_follow_links(self, auth_user):
        if auth_user is None:
            auth_user = self._request.user
        return auth_user.has_perm('dz.follow_news')

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_news')

    crawl_action = 'news'

    def content_cut(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/news_content_cut.html',
                               context=dict(news=obj, opts=self.opts))
        return tpl.rendered_content
    content_cut.short_description = _('news cut (column)')
    content_cut.admin_order_field = 'preamble'

    def archived_str(self, obj):
        return _('Archived') if obj.archived else _('Fresh')
    archived_str.short_description = _('archived (column)')
    archived_str.admin_order_field = 'archived'

    def link_str(self, obj):
        if self.user_can_follow_links(None):
            return format_html(
                '<a href="{link}" target="_blank">{link}</a>',
                link=obj.link
            )
        else:
            return obj.link
    link_str.short_description = _('news link (column)')
    link_str.admin_order_field = 'link'

    def get_urls(self):
        news_content_url = url(
            r'^(?P<id>\d+)/news-content/$',
            self.admin_site.admin_view(self.news_content_view),
            name='%s_%s_news_content' % (self.opts.app_label, self.opts.model_name)
        )
        data_table_img_url = url(
            r'^\d+/news-content/img/(?P<path>.*)$',
            self.data_table_img_view
        )
        orig_urls = super(NewsAdmin, self).get_urls()
        return [news_content_url, data_table_img_url] + orig_urls

    def news_content_view(self, request, id):
        news = self.get_object(request, id)
        if news:
            context = {
                'news': news,
                'can_follow_links': self.user_can_follow_links(request.user),
            }
            return TemplateResponse(request, 'admin/dz/news_content_popup.html', context)
        else:
            return HttpResponseNotFound()

    def data_table_img_view(self, request, path):
        path = re.sub('/change/$', '', path).replace('kladionice/', 'bookmaker-')
        new_path = settings.STATIC_URL + settings.WEBPACK_SUBDIR + '/' + path
        return HttpResponsePermanentRedirect(new_path)
