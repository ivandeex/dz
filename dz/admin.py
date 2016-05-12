from django.contrib import admin
from . import models

admin.site.site_header = admin.site.site_title = 'DZ!'


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ['id', 'published', 'place', 'title', 'tip_block',
                    'result', 'tipster', 'coeff', 'min_coeff',
                    'stake', 'due', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'details_url', 'archived']
    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False


@admin.register(models.Crawl)
class CrawlAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'action', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'started', 'host']
    list_per_page = 20
    ordering = ['-id']

    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False
