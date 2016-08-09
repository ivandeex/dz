"""
Root URL Configuration
"""

from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf import settings
from dz.admin import site as dz_admin_site

urlpatterns = i18n_patterns(
    url(r'^dz/admin/', dz_admin_site.urls, name='dz-admin'),
    url(r'^dz/', include('dz.urls', namespace='dz')),
    url(r'^admin/', admin.site.urls, name='django-admin'),
)

urlpatterns += [
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
elif settings.HEROKU:
    from django.views.static import serve
    pattern = r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/')
    urlpatterns += [url(pattern, serve, {'document_root': settings.STATIC_ROOT})]
