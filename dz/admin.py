from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http import HttpResponseRedirect
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
    can_crawl = can_export = False

    class Media:
        css = {'all': ['dz/dz-changelist.css', 'dz/dz-results.css']}
        js = ['dz/dz.js']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def changelist_view(self, request, extra_context=None):
        tpl_resp = super(DzModelAdmin, self).changelist_view(request, extra_context)
        tpl_resp.context_data.update({
            'title': _(self.opts.verbose_name_plural.title()),  # override title
            'can_crawl': self.can_crawl,
            'can_export': self.can_export,
        })
        return tpl_resp


class DzCrawlModelAdmin(ExportMixin, DzModelAdmin):
    change_list_template = 'admin/dz/change_list.html'
    formats = [base_formats.XLSX]
    can_crawl = can_export = True

    def get_urls(self):
        urls = super(DzCrawlModelAdmin, self).get_urls()
        my_urls = [url(r'^crawl/$', self.admin_site.admin_view(self.crawl_view),
                       name='%s_%s_crawl' % (self.opts.app_label, self.opts.model_name))]
        return my_urls + urls

    def crawl_view(self, request, extra_context=None):
        opts = self.opts
        if self.can_crawl:
            message = '%s crawling started!' % opts.verbose_name_plural.title()
            self.message_user(request, _(message))
        url = reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                      current_app=self.admin_site.name)
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
    exclude = ['subtable']
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']


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
    date_hierarchy = 'published'
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']


class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'action', 'type', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'host']
    date_hierarchy = 'started'
    radio_fields = {'action': admin.HORIZONTAL, 'type': admin.HORIZONTAL}
    ordering = ['-id']


class UserAdmin(DzModelAdmin):
    list_display = ['username', 'is_admin']
    list_filter = ['is_admin']
    ordering = ['username']

    def has_add_permission(self, request):
        return request.user.is_superuser


class DzAdminSite(admin.AdminSite):
    site_header = _('D.Z.')
    site_title = _('D.Z.')
    index_title = _('Index:')
    site_url = None

site = DzAdminSite(name='dz-admin')
site.register(models.News, NewsAdmin)
site.register(models.Tip, TipAdmin)
site.register(models.Crawl, CrawlAdmin)
site.register(models.User, UserAdmin)
