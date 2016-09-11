from __future__ import unicode_literals, absolute_import
from django.template.response import TemplateResponse
from django.http import HttpResponseNotFound
from django.conf import settings
from django.conf.urls import url
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from .common import DzCrawlModelAdmin, DzExportResource
from .common import DzSelectFieldListFilter, DzArchivedListFilter
from .. import models


class TipExportResource(DzExportResource):
    class Meta:
        model = models.Tip
        exclude = ['text']


class TipAdmin(DzCrawlModelAdmin):
    resource_class = TipExportResource

    list_display = ['id', 'published', 'league', 'parties', 'content_cut',
                    'result', 'tipster', 'odds', 'min_odds',
                    'stake', 'earnings', 'spread', 'bookmaker', 'success_str',
                    'updated', 'crawled', 'link_str', 'archived_str']
    if settings.NARROW_GRIDS:
        list_display = ['id', 'published', 'place', 'title', 'content_cut',
                        'result', 'tipster', 'archived']
    list_filter = [('league', DzSelectFieldListFilter),
                   ('parties', DzSelectFieldListFilter),
                   ('tipster', DzSelectFieldListFilter),
                   DzArchivedListFilter,
                   ]
    search_fields = ['parties', 'title', 'text']
    exclude = ['text']
    date_hierarchy = 'published'
    ordering = ['-published', '-id']

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_tips')

    def user_can_follow_links(self, auth_user):
        if auth_user is None:
            auth_user = self._request.user
        return auth_user.has_perm('dz.follow_tips')

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_tips')

    crawl_action = 'tips'

    def content_cut(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/tip_content_cut.html',
                               context=dict(tip=obj, opts=self.opts))
        return tpl.rendered_content
    content_cut.short_description = _('tip cut (column)')
    content_cut.admin_order_field = 'title'

    SUCCESS_CODE_MAP = {
        'unknown': _('(success) unknown'),
        'hit': _('(success) hit'),
        'miss': _('(success) miss'),
    }

    def success_str(self, obj):
        return self.SUCCESS_CODE_MAP.get(obj.success, obj.success)
    success_str.short_description = _('tip success (column)')
    success_str.admin_order_field = 'success'

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
    link_str.short_description = _('tip link (column)')
    link_str.admin_order_field = 'link'

    def get_urls(self):
        tip_content_url = url(
            r'^(?P<id>\d+)/tip-content/$',
            self.admin_site.admin_view(self.tip_content_view),
            name='%s_%s_tip_content' % (self.opts.app_label, self.opts.model_name))
        return [tip_content_url] + super(TipAdmin, self).get_urls()

    def tip_content_view(self, request, id):
        tip = self.get_object(request, id)
        if tip:
            return TemplateResponse(request, 'admin/dz/tip_content_popup.html',
                                    dict(tip=tip, is_popup=True))
        else:
            return HttpResponseNotFound()
