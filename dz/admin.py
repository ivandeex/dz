from django.contrib import admin
from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Tip)
class TipAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Crawl)
class CrawlAdmin(admin.ModelAdmin):
    pass
