from django.conf.urls import url
from . import views, api

app_name = 'dz'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/crawl/job/?$', api.api_crawl_job),
    url(r'^api/crawl/item/?$', api.api_crawl_item),
    url(r'^api/crawl/complete/?$', api.api_crawl_complete),
]
