from django.contrib import admin
from . import models

admin.site.site_header = admin.site.site_title = 'D.Z.'
admin.site.index_title = 'Index:'
admin.site.site_url = None


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 50
    actions = None

    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(models.News)
class NewsAdmin(DzModelAdmin):
    list_display = ['id', 'published', 'section', 'subsection',
                    'short_title', 'title', 'col_content',
                    'updated', 'crawled', 'url', 'archived']
    list_filter = ['published', 'updated',
                   # 'section', 'subsection',
                   'archived']
    search_fields = ['short_title', 'title', 'preamble', 'content']
    exclude = ['subtable']
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']


@admin.register(models.Tip)
class TipAdmin(DzModelAdmin):
    list_display = ['id', 'published', 'place', 'title', 'col_tip',
                    'result', 'tipster', 'coeff', 'min_coeff',
                    'stake', 'due', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'details_url', 'archived']
    list_filter = ['published', 'updated',
                   # 'place', 'title', 'tipster',
                   'archived']
    search_fields = ['title', 'tip', 'text']
    radio_fields = {'archived': admin.HORIZONTAL}
    ordering = ['-published', '-id']


@admin.register(models.Crawl)
class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'action', 'type', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'started', 'host']
    radio_fields = {'action': admin.HORIZONTAL, 'type': admin.HORIZONTAL}
    ordering = ['-id']


@admin.register(models.User)
class UserAdmin(DzModelAdmin):
    list_display = ['username', 'is_admin']
    list_filter = ['is_admin']
    ordering = ['username']

    def has_add_permission(self, request):
        return request.user.is_superuser
