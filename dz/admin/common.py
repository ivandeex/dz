from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from import_export.resources import ModelResource
from ..models import Crawl


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
            return queryset.filter(archived=False)  # Filter by "fresh" if default (None)
        if self.value() == 'a':
            return queryset.filter(archived=True)


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 50
    # actions = None
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
        if hasattr(tpl_resp, 'context_data'):
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
    crawl_action = None

    def get_urls(self):
        urls = super(DzCrawlModelAdmin, self).get_urls()
        wrap = self.admin_site.admin_view
        rev_fmt = self.opts.app_label, self.opts.model_name
        crawl_url = url(r'^crawl/$', wrap(self.crawl_view), name='%s_%s_crawl' % rev_fmt)
        return [crawl_url] + urls

    def crawl_view(self, request, extra_context=None):
        opts = self.opts
        if self.crawl_action and self.user_can_crawl(request.user):
            status = Crawl.add_manual_crawl(self.crawl_action)
            self.message_user(request, _('Crawling %s!' % status))
        rev_fmt = opts.app_label, opts.model_name
        url = reverse('admin:%s_%s_changelist' % rev_fmt, current_app=self.admin_site.name)
        filter_kwargs = dict(opts=opts, preserved_filters=self.get_preserved_filters(request))
        return HttpResponseRedirect(add_preserved_filters(filter_kwargs, url))


class DzExportResource(ModelResource):
    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        field = super(DzExportResource, cls)\
            .field_from_django_field(field_name, django_field, readonly)
        field.column_name = django_field.verbose_name
        return field
