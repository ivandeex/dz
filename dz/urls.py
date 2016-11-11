from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views, tables, api

app_name = 'dz'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.login,
        {'template_name': 'dz/tables/login.html'}, name='login'),

    url(r'^tables/news/$', tables.news_list_view, name='news-list'),
    url(r'^tables/news/export/$', tables.news_export_view, name='news-export'),
    url(r'^tables/newsbox/(?P<pk>\d+)/$', tables.newsbox_view, name='newsbox-popup'),
    url(r'^tables/newsbox/\d+/img/(?P<path>.*)$', tables.newsbox_img_redirect),
    url(r'^tables/news/(?P<pk>\d+)/$', tables.form_view,
        {'form_class': tables.NewsForm, 'next': 'news-list', 'admin_only': False},
        name='news-form'),

    url(r'^tables/tip/$', tables.tip_list_view, name='tip-list'),
    url(r'^tables/tip/export/$', tables.tip_export_view, name='tip-export'),
    url(r'^tables/tipbox/(?P<pk>\d+)/$', tables.tipbox_view, name='tipbox-popup'),
    url(r'^tables/tip/(?P<pk>\d+)/$', tables.form_view,
        {'form_class': tables.TipForm, 'next': 'tip-list', 'admin_only': False},
        name='tip-form'),

    url(r'^tables/crawl/$', tables.crawl_list_view, name='crawl-list'),
    url(r'^tables/crawl/(?P<pk>\d+)/$', tables.form_view,
        {'form_class': tables.CrawlForm, 'next': 'crawl-list', 'admin_only': True},
        name='crawl-form'),

    url(r'^tables/user/$', tables.user_list_view, name='user-list'),
    url(r'^tables/user/(?P<pk>\d+)/$', tables.form_view,
        {'form_class': tables.UserForm, 'next': 'user-list', 'admin_only': True},
        name='user-form'),

    url(r'^tables/schedule/$', tables.schedule_list_view, name='schedule-list'),
    url(r'^tables/schedule/(?P<pk>\d+)/$', tables.form_view,
        {'form_class': tables.ScheduleForm, 'next': 'schedule-list', 'admin_only': True},
        name='schedule-form'),

    url(r'^tables/action/crawl/$', tables.crawl_action_view, name='crawl-action'),
    url(r'^tables/action/row/$', tables.row_action_view, name='row-action'),

    url(r'^api/crawl/job/?$', api.api_crawl_job, name='api-job'),
    url(r'^api/crawl/item/?$', api.api_crawl_item, name='api-item'),
    url(r'^api/crawl/complete/?$', api.api_crawl_complete, name='api-complete'),
]
