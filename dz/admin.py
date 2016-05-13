from django.contrib import admin
from . import models

admin.site.site_header = admin.site.site_title = 'DZ!'


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 20

    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False


@admin.register(models.User)
class UserAdmin(DzModelAdmin):
    list_display = ['username', 'is_admin']
    def has_add_permission(self, request):
        return True


@admin.register(models.News)
class NewsAdmin(DzModelAdmin):
    list_display = ['id', 'published', 'section', 'subsection',
                    'short_title', 'title', 'content_cut',
                    'updated', 'crawled', 'url', 'archived']


@admin.register(models.Tip)
class TipAdmin(DzModelAdmin):
    list_display = ['id', 'published', 'place', 'title', 'tip_block',
                    'result', 'tipster', 'coeff', 'min_coeff',
                    'stake', 'due', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'details_url', 'archived']


@admin.register(models.Crawl)
class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'action', 'type', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'started', 'host']
    ordering = ['-id']
