from __future__ import unicode_literals, absolute_import
from django.contrib import admin
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

    list_display = ['id', 'published', 'place', 'title', 'col_tip',
                    'result', 'tipster', 'coeff', 'min_coeff',
                    'stake', 'due', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'details_url', 'archived']
    if settings.NARROW_GRIDS:
        list_display = ['id', 'published', 'place', 'title', 'col_tip',
                        'result', 'tipster', 'archived']
    list_filter = [('place', DzSelectFieldListFilter),
                   ('title', DzSelectFieldListFilter),
                   ('tipster', DzSelectFieldListFilter),
                   DzArchivedListFilter,
                   ]
    search_fields = ['title', 'tip', 'text']
    exclude = ['text']
    date_hierarchy = 'published'
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_tips')

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_tips')

    crawl_action = 'tips'

    def col_tip(self, obj):
        tpl = TemplateResponse(self._request, 'admin/dz/tip_text_col.html',
                               context=dict(obj=obj, opts=self.opts))
        return tpl.rendered_content
    col_tip.short_description = _('short tip')
    col_tip.admin_order_field = 'tip'

    def get_urls(self):
        tip_text_url = url(r'^(?P<id>\d+)/tip_text/$',
                           self.admin_site.admin_view(self.tip_text_view),
                           name='%s_%s_tip_text' % (self.opts.app_label, self.opts.model_name))
        return [tip_text_url] + super(TipAdmin, self).get_urls()

    def tip_text_view(self, request, id):
        obj = self.get_object(request, id)
        if obj:
            return TemplateResponse(request, 'admin/dz/tip_text_popup.html',
                                    dict(obj=obj, is_popup=True))
        else:
            return HttpResponseNotFound()
