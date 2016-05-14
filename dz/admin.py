from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http import HttpResponseRedirect
from . import models


admin.site.site_header = admin.site.site_title = 'D.Z.'
admin.site.index_title = 'Index:'
admin.site.site_url = None


class DzSelectFieldListFilter(admin.AllValuesFieldListFilter):
    template = 'admin/dz/list_filter.html'


class DzArchivedListFilter(admin.SimpleListFilter):
    title = _('Archived')
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
    can_crawl = False

    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_crawl_permission(self, request):
        return self.can_crawl and self.has_change_permission(request)

    def get_urls(self):
        urls = super(DzModelAdmin, self).get_urls()
        if self.can_crawl:
            wrap = self.admin_site.admin_view
            info = (self.opts.app_label, self.opts.model_name)
            extra_urls = [url(r'^crawl/$', wrap(self.crawl_view), name='%s_%s_crawl' % info)]
            urls = extra_urls + urls
        return urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'title': _(self.opts.verbose_name_plural.title()),
            'has_crawl_permission': self.has_crawl_permission(request),
        })
        print self.model, extra_context
        return super(DzModelAdmin, self).changelist_view(request, extra_context)

    def crawl_view(self, request, extra_context=None):
        opts = self.opts
        if self.has_crawl_permission(request):
            message = '%s crawling started!' % opts.verbose_name_plural.title()
            self.message_user(request, _(message))
        url = reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                      current_app=self.admin_site.name)
        preserved_filters = self.get_preserved_filters(request)
        url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, url)
        return HttpResponseRedirect(url)


@admin.register(models.News)
class NewsAdmin(DzModelAdmin):
    can_crawl = True
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


@admin.register(models.Tip)
class TipAdmin(DzModelAdmin):
    can_crawl = True
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
                   'updated',
                   ]
    search_fields = ['title', 'tip', 'text']
    date_hierarchy = 'published'
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']


@admin.register(models.Crawl)
class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'action', 'type', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'started', 'host']
    date_hierarchy = 'started'
    radio_fields = {'action': admin.HORIZONTAL, 'type': admin.HORIZONTAL}
    ordering = ['-id']


@admin.register(models.User)
class UserAdmin(DzModelAdmin):
    list_display = ['username', 'is_admin']
    list_filter = ['is_admin']
    ordering = ['username']

    def has_add_permission(self, request):
        return request.user.is_superuser
