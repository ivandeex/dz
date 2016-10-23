from django.urls import reverse
from django.test import override_settings, tag
from . import base, views


class AdminTestsMixin(views.ListViewTestsMixin):
    def test_unauthorized_request_should_redirect_to_login(self):
        for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
            list_url = reverse('dz-admin:dz_%s_changelist' % model_name)
            login_url = '%s?next=%s' % (reverse('dz-admin:login'), list_url)
            response = self.client.get(list_url)
            self.assertRedirects(response, login_url)

    def _test_table_view(self, user_name, model_name,
                         can_access=True, can_crawl=None,
                         can_use_row_actions=None):
        info = ' (user: {}, model: {})'.format(user_name, model_name)
        list_url = reverse('dz-admin:dz_%s_changelist' % model_name)
        response = self.client.get(list_url)

        if not can_access:
            self.assertEquals(response.status_code, 403)
            return

        self.assertContains(response, '>{}</'.format(user_name),
                            msg_prefix='user name should be in the top menu' + info)

        self.assertContains(response, '>Current time (%s):</' % self.cur_tz_name,
                            msg_prefix='current time should be visible' + info)

        model_name_plural = model_name + ('' if model_name == 'news' else 's')
        crawl_button_text = '>Crawl %s</' % model_name_plural
        if can_crawl is True:
            self.assertContains(response, crawl_button_text,
                                msg_prefix='crawl button should be present' + info)
        elif can_crawl is False:
            self.assertNotContains(response, crawl_button_text,
                                   msg_prefix='crawl button should not be present' + info)


@tag('admin')
@override_settings(DZ_SKIN='django')
class DjangoSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_settings(DZ_SKIN='plus')
class PlusSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_settings(DZ_SKIN='grappelli')
class GrappelliSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass


@tag('admin')
@override_settings(DZ_SKIN='bootstrap')
class BootstrapSkinAdminTests(base.BaseDzTestCase, AdminTestsMixin):
    pass
