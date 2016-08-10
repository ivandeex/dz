from django.conf.urls import url
from . import views

app_name = 'dz'
urlpatterns = [
    url(r'^$', views.index)
]
