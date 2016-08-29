from __future__ import unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from import_export.resources import ModelResource
from . import models


class DzSelectFieldListFilter(admin.AllValuesFieldListFilter):
    template = 'admin/dz/list_filter.html'


class DzArchivedListFilter(admin.SimpleListFilter):
    title = _('archive filter')
    parameter_name = 'arch'

    def lookups(self, request, model_admin):
        return [
            ('-', _('All')),        # The "All" choice is not default (None)
            ('a', _('Archived')),
            ('f', _('Fresh')),
        ]

    def choices(self, changelist):
        choices = super(DzArchivedListFilter, self).choices(changelist)
        return list(choices)[1:]   # Skip the All (None) choice

    def queryset(self, request, queryset):
        if self.value() is None or self.value() == 'f':
            return queryset.filter(archived='fresh')  # Filter by "fresh" if default (None)
        if self.value() == 'a':
            return queryset.filter(archived='archived')


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 50
    actions = None
    can_export = False
    _get_readonly_fields_called = False

    # class Media:
    #     css = {'all': ['dz/admin/changelist.css', 'dz/admin/results.css']}
    #     js = ['dz/admin/filter.js']

    def user_is_readonly(self, auth_user):
        return False

    def user_can_crawl(self, auth_user):
        return False

    def get_list_display_links(self, request, list_display):
        if self.user_is_readonly(request.user):
            return None
        return super(DzModelAdmin, self).get_list_display_links(request, list_display)

    def get_readonly_fields(self, request, obj=None):
        if self._get_readonly_fields_called or not self.user_is_readonly(request.user):
            return super(DzModelAdmin, self).get_readonly_fields(request, obj)
        try:
            self._get_readonly_fields_called = True
            return self.get_fields(request, obj)
        finally:
            self._get_readonly_fields_called = False

    def changelist_view(self, request, extra_context=None):
        request.current_app = self.admin_site.name
        self._request = request
        tpl_resp = super(DzModelAdmin, self).changelist_view(request, extra_context)
        tpl_resp.context_data.update({
            'title': _(self.opts.verbose_name_plural.title()),  # override title
            'can_crawl': self.user_can_crawl(request.user),
            'can_export': self.can_export,
        })
        return tpl_resp


class DzCrawlModelAdmin(ExportMixin, DzModelAdmin):
    change_list_template = 'admin/dz/change_list.html'
    formats = [base_formats.XLSX]
    can_export = True

    def get_urls(self):
        urls = super(DzCrawlModelAdmin, self).get_urls()
        wrap = self.admin_site.admin_view
        rev_fmt = self.opts.app_label, self.opts.model_name
        crawl_url = url(r'^crawl/$', wrap(self.crawl_view), name='%s_%s_crawl' % rev_fmt)
        return [crawl_url] + urls

    def crawl_view(self, request, extra_context=None):
        opts = self.opts
        if self.user_can_crawl(request.user):
            message = '%s crawling started!' % opts.verbose_name_plural.title()
            self.message_user(request, _(message))
        rev_fmt = opts.app_label, opts.model_name
        url = reverse('admin:%s_%s_changelist' % rev_fmt, current_app=self.admin_site.name)
        url = add_preserved_filters(
            {'preserved_filters': self.get_preserved_filters(request), 'opts': opts}, url)
        return HttpResponseRedirect(url)


class DzExportResource(ModelResource):
    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        field = super(DzExportResource, cls)\
            .field_from_django_field(field_name, django_field, readonly)
        field.column_name = django_field.verbose_name
        return field


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


class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'action', 'type', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'host']
    date_hierarchy = 'started'
    radio_fields = {'action': admin.HORIZONTAL, 'type': admin.HORIZONTAL}
    ordering = ['-id']


class UserAdmin(DzModelAdmin):
    fields = ['username', 'password', 'is_admin']
    list_display = ['username', 'is_admin']
    list_filter = ['is_admin']
    ordering = ['username']

    def has_add_permission(self, request):
        return request.user.is_superuser


class DzAdminSite(admin.AdminSite):
    site_header = _('D.Z.')
    site_title = _('D.Z.')
    index_title = _('Index:')

    def index(self, request, extra_context=None):
        # url = reverse('admin:app_list', kwargs={'app_label': 'dz'}, current_app=self.name)
        return redirect('%s:app_list' % self.name, app_label='dz')

    def each_context(self, request):
        context = super(DzAdminSite, self).each_context(request)
        apps = context['available_apps']
        models = apps[0]['models'] if apps else []  # can be empty if not logged in
        context['dz_models'] = [dict(name=m['name'], url=m['admin_url']) for m in models]
        return context


site = DzAdminSite(name='dz-admin')
site.register(models.News, NewsAdmin)
site.register(models.Tip, TipAdmin)
site.register(models.Crawl, CrawlAdmin)
site.register(models.User, UserAdmin)
