"""
dzproj URL Configuration
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index)
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
