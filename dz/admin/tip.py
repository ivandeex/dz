from __future__ import unicode_literals, absolute_import
from django.template.response import TemplateResponse
from django.http import HttpResponseNotFound
from django.conf.urls import url
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .common import DzCrawlModelAdmin, DzExportResource
from .common import DzSelectFieldListFilter, DzArchivedListFilter
from .. import models, helpers


class TipExportResource(DzExportResource):
    class Meta:
        model = models.Tip
        exclude = ['text']


class TipAdmin(DzCrawlModelAdmin):
    resource_class = TipExportResource

    list_display = [
        'id', 'published', 'league', 'parties', 'description_str',
        'result', 'tipster', 'odds', 'min_odds',
        'stake', 'earnings', 'spread', 'bookmaker', 'success_str',
        'updated', 'crawled', 'link_str', 'archived_str'
    ]

    list_filter = [
        DzArchivedListFilter,
        ('tipster', DzSelectFieldListFilter),
        ('league', DzSelectFieldListFilter),
        ('parties', DzSelectFieldListFilter),
    ]

    search_fields = ['parties', 'title', 'text']
    exclude = ['text']
    date_hierarchy = 'published'
    ordering = ['-published', '-id']

    crawl_action = 'tips'

    def user_can_crawl(self, auth_user):
        return auth_user.has_perm('dz.crawl_tips')

    def user_is_readonly(self, auth_user):
        return auth_user.has_perm('dz.view_tips')

    def user_can_follow_links(self, auth_user):
        return (auth_user or self._request.user).has_perm('dz.follow_tips')

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
        return helpers.format_external_link(self._request, obj.link)
    link_str.short_description = _('tip link (column)')
    link_str.admin_order_field = 'link'

    def description_str(self, obj):
        skin = settings.DZ_SKIN
        if skin != 'bootstrap':
            skin = 'admin'
        template = 'admin/dz-%s/tip-description.html' % skin
        tpl = TemplateResponse(self._request, template, dict(tip=obj, opts=self.opts))
        return tpl.rendered_content
    description_str.short_description = _('tip cut (column)')
    description_str.admin_order_field = 'title'

    def get_urls(self):
        tipbox_url = url(
            r'^(?P<pk>\d+)/tipbox/$',
            self.admin_site.admin_view(self.tipbox_view),
            name='%s_%s_tipbox' % (self.opts.app_label, self.opts.model_name))
        return [tipbox_url] + super(TipAdmin, self).get_urls()

    def tipbox_view(self, request, pk):
        tip = self.get_object(request, pk)
        if not tip:
            return HttpResponseNotFound()
        skin = settings.DZ_SKIN
        if skin == 'grappelli':
            is_popup = False
        elif skin == 'bootstrap':
            is_popup = True
        else:
            skin, is_popup = 'plus', True
        template = 'admin/dz-%s/tipbox-popup.html' % skin
        is_ajax = bool(request.is_ajax() or request.GET.get('_ajax'))
        context = dict(tip=tip, is_popup=is_popup, is_ajax=is_ajax)
        return TemplateResponse(request, template, context)
