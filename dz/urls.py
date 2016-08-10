from django.conf.urls import url
from . import views as dz_views

app_name = 'dz'
urlpatterns = [
    url(r'^$', dz_views.index, name='index'),
]
