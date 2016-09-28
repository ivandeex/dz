from django.conf.urls import url
from . import views, tables, api

app_name = 'dz'
urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^tables/news/$', tables.news_list_view, name='news-list'),
    url(r'^tables/newsbox/(?P<pk>\d+)/$', tables.newsbox_view, name='newsbox-popup'),
    url(r'^tables/newsbox/\d+/img/(?P<path>.*)$', tables.newsbox_img_redirect),

    url(r'^tables/tip/$', tables.tip_list_view, name='tip-list'),
    url(r'^tables/tipbox/(?P<pk>\d+)/$', tables.tipbox_view, name='tipbox-popup'),

    url(r'^tables/crawl/$', tables.crawl_list_view, name='crawl-list'),
    url(r'^tables/user/$', tables.user_list_view, name='user-list'),
    url(r'^tables/schedule/$', tables.schedule_list_view, name='schedule-list'),

    url(r'^tables/action/crawl/$', tables.crawl_action_view, name='crawl-action'),

    url(r'^api/crawl/job/?$', api.api_crawl_job),
    url(r'^api/crawl/item/?$', api.api_crawl_item),
    url(r'^api/crawl/complete/?$', api.api_crawl_complete),
]
