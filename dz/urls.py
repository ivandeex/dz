"""
dzproj URL Configuration
"""
import re
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings

from . import views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index)
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

if settings.HEROKU:
    from django.views.static import serve
    static_pattern = r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/')
    urlpatterns += [url(static_pattern, serve, kwargs=dict(document_root=settings.STATIC_ROOT))]
