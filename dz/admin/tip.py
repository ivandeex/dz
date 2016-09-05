from __future__ import unicode_literals, absolute_import
from django.template.response import TemplateResponse
from django.http import HttpResponseNotFound
from django.conf import settings
from django.conf.urls import url
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
                    'result', 'tipster', 'rate', 'minrate',
                    'stake', 'earnings', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'link', 'archived_str']
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

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_tips')

    crawl_action = 'tips'

    def content_cut(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/tip_content_cut.html',
                               context=dict(tip=obj, opts=self.opts))
        return tpl.rendered_content
    content_cut.short_description = _('tip cut')
    content_cut.admin_order_field = 'title'

    def archived_str(self, obj):
        return _('Archived') if obj.archived else _('Fresh')
    archived_str.short_description = _('archived')
    archived_str.admin_order_field = 'archived'

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
