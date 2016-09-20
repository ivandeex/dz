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


class NewsAdmin(DzCrawlModelAdmin):
    resource_class = NewsExportResource

    list_display = ['id', 'published', 'sport', 'league',
                    'parties', 'title', 'description_str',
                    'updated', 'crawled', 'link_str', 'archived_str']

    list_filter = [('sport', DzSelectFieldListFilter),
                   ('league', DzSelectFieldListFilter),
                   DzArchivedListFilter,
                   'updated',
                   ]

    search_fields = ['parties', 'title',
                     'newstext__preamble', 'newstext__content']

    date_hierarchy = 'published'
    ordering = ['-published', '-id']

    crawl_action = 'news'

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_news')

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_news')

    def user_can_follow_links(self, auth_user):
        return (auth_user or self._request.user).has_perm('dz.follow_news')

    def description_str(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz-admin/news_description.html',
                               context=dict(news=obj, opts=self.opts))
        return tpl.rendered_content
    description_str.short_description = _('news cut (column)')
    description_str.admin_order_field = 'preamble'

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
        newsbox_url = url(
            r'^(?P<pk>\d+)/newsbox/$',
            self.admin_site.admin_view(self.newsbox_view),
            name='%s_%s_news_content' % (self.opts.app_label, self.opts.model_name)
        )
        data_table_img_url = url(
            r'^\d+/newsbox/img/(?P<path>.*)$',
            self.data_table_img_view
        )
        orig_urls = super(NewsAdmin, self).get_urls()
        return [newsbox_url, data_table_img_url] + orig_urls

    def newsbox_view(self, request, pk):
        news = self.get_object(request, pk)
        if news:
            context = {
                'news': news,
                'can_follow_links': self.user_can_follow_links(request.user),
            }
            return TemplateResponse(request, 'admin/dz-admin/newsbox_popup.html', context)
        else:
            return HttpResponseNotFound()

    def data_table_img_view(self, request, path):
        path = re.sub('/change/$', '', path)
        new_path = settings.STATIC_URL + settings.WEBPACK_SUBDIR + '/' + path
        return HttpResponsePermanentRedirect(new_path)
