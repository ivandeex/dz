from django.contrib import admin
from . import models

admin.site.site_header = admin.site.site_title = 'DZ!'


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    class Media:
        css = {'all': ['dz.css']}

    def has_add_permission(self, request):
        return False


@admin.register(models.User)
class UserAdmin(DzModelAdmin):
    def has_add_permission(self, request):
        import ipdb; ipdb.set_trace()
        return True


@admin.register(models.News)
class NewsAdmin(DzModelAdmin):
    pass


@admin.register(models.Tip)
class TipAdmin(DzModelAdmin):
    list_display = ['id', 'published', 'place', 'title', 'tip_block',
                    'result', 'tipster', 'coeff', 'min_coeff',
                    'stake', 'due', 'spread', 'betting', 'success',
                    'updated', 'crawled', 'details_url', 'archived']


@admin.register(models.Crawl)
class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'type', 'action', 'status', 'started', 'ended',
                    'news', 'tips', 'host', 'ipaddr', 'pid']
    list_filter = ['type', 'action', 'status', 'started', 'host']
    ordering = ['-id']
