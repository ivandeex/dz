from django.urls import reverse
from django.conf import settings
from django.test import override_settings, tag
from . import base, views

ADMIN_LOGIN_URL = 'dz-admin:login'


class AdminTestsMixin(views.ListViewTestsMixin):

    def test_unauthorized_request_should_redirect_to_login(self):
        for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
            list_url = reverse('dz-admin:dz_%s_changelist' % model_name)
            login_url = '%s?next=%s' % (reverse(ADMIN_LOGIN_URL), list_url)
            response = self.client.get(list_url)
            self.assertRedirects(response, login_url)

    def _test_table_view(self, user_name, model_name,
                         can_access=True, can_crawl=None, can_export=None,
                         can_use_row_actions=None):
        skin = settings.DZ_SKIN
        info = ' (user: {}, model: {})'.format(user_name, model_name)
        list_url = reverse('dz-admin:dz_%s_changelist' % model_name)
        response = self.client.get(list_url)

        if not can_access:
            self.assertEquals(response.status_code, 403)
            return

        self.assertContains(response, '>{}</'.format(user_name),
                            msg_prefix='user name should be in the top menu' + info)

        if skin in ('grappelli', 'plus', 'bootstrap'):
            self._page_should_load_custom_js_css(response, info, 'prod', skin)

            self.assertContains(response, '>Current time (%s):</' % self.cur_tz_name,
                                msg_prefix='current time should be visible' + info)

        model_name_plural = model_name + ('' if model_name == 'news' else 's')
        crawl_button_text = '>Crawl %s</' % model_name_plural
        if can_crawl is True:
            self.assertContains(response, crawl_button_text,
                                msg_prefix='crawl button should be present' + info)
        if can_crawl is False:
            self.assertNotContains(response, crawl_button_text,
                                   msg_prefix='crawl button should not be present' + info)

        export_button_text = '>Export</'
        if can_export is True:
            self.assertContains(response, export_button_text,
                                msg_prefix='export button should be present' + info)
        if can_export is False:
            self.assertNotContains(response, export_button_text,
                                   msg_prefix='export button should not be present' + info)


class override_dz_skin(override_settings):
    """
    When DZ admin skin is 'django' or 'plus', the 'dz' application must
    be the first so that our 'base_site' template takes precendence.
    When the skin is 'grappelli' or 'bootstrap', the code in `settings.py`
    prepend them in the INSTALLED_APPS list, and their 'base_site.html'
    takes over.

    Since we manipulate skin on the fly, we must amend INSTALLED_APPS
    and refix application order when a test case starts.
    The base `override_settings` will take care of such low level tasks
    clearing app directories and other caches.

    See also: `REORDER INSTALLED APPS` in `settings.py`
    """
    def __init__(self, **kwargs):
        DZ_SKIN = kwargs['DZ_SKIN']
        INSTALLED_APPS = settings.INSTALLED_APPS[:]

        if INSTALLED_APPS[0] != 'dz':
            assert INSTALLED_APPS[1] == 'dz'
            assert INSTALLED_APPS[0] in ('grappelli', 'django_admin_bootstrapped')
            del INSTALLED_APPS[0]
        if DZ_SKIN == 'grappelli':
            INSTALLED_APPS.insert(0, 'grappelli')
        if DZ_SKIN == 'bootstrap':
            INSTALLED_APPS.insert(0, 'django_admin_bootstrapped')

        if INSTALLED_APPS != settings.INSTALLED_APPS:
            kwargs['INSTALLED_APPS'] = INSTALLED_APPS

        super(override_dz_skin, self).__init__(**kwargs)


@tag('admin')
@override_dz_skin(DZ_SKIN='django')
class DjangoSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_dz_skin(DZ_SKIN='plus')
class PlusSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_dz_skin(DZ_SKIN='grappelli')
class GrappelliSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_dz_skin(DZ_SKIN='bootstrap')
class BootstrapSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass
