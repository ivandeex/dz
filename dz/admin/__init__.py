from __future__ import unicode_literals, absolute_import
from django.contrib import admin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from .common import DzModelAdmin
from .crawl import CrawlAdmin
from .news import NewsAdmin
from .tip import TipAdmin
from .. import models


class ScheduleAdmin(DzModelAdmin):
    list_display = ['time', 'target']
    ordering = ['time', 'target']


class UserAdmin(DzModelAdmin):
    fields = ['username', 'password', 'is_admin', 'can_follow']
    list_display = ['username', 'is_admin', 'can_follow']
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
site.register(models.Schedule, ScheduleAdmin)
site.register(models.User, UserAdmin)
