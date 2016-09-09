from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect
from dz import admin as dz_admin

urlpatterns = [
]

urlpatterns_i18n = [
    url(r'^admin/', admin.site.urls),
    url(r'^dz/admin/', dz_admin.site.urls),
    url(r'^dz/', include('dz.urls', namespace='dz')),
    url(r'^$', lambda request: redirect('dz:index')),
]

urlpatterns_setlang = [url(r'^i18n/', include('django.conf.urls.i18n'))]

urlpatterns_i18n += urlpatterns_setlang
urlpatterns += i18n_patterns(*urlpatterns_i18n)

if settings.DEBUG and settings.USE_I18N:
    urlpatterns += [url(r'^rosetta/', include('rosetta.urls'))]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
