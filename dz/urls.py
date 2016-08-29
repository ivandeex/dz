from django.conf.urls import url
from . import views

app_name = 'dz'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/spider/run/$', views.api_spider_run, name='api-spider-run'),
    url(r'^api/spider/results/$', views.api_spider_results, name='api-spider.reults')
]
