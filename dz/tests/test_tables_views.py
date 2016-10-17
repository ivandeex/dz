from django.test import tag
from django.urls import reverse
from . import base, views


@tag('views')
class TableViewsTests(base.BaseDzTestCase, views.ListViewTestsMixin):
    def test_unauthorized_request_should_redirect_to_login(self):
        for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
            list_url = reverse('dz:%s-list' % model_name)
            response = self.client.get(list_url)
            self.assertRedirects(
                response,
                '/accounts/login/?next=' + list_url,
                fetch_redirect_response=False  # because it currently returns 404
            )

    def _test_table_view(self, user_name, model_name, can_access=True, can_crawl=None):
        info = ' (user: {}, model: {})'.format(user_name, model_name)
        list_url = reverse('dz:%s-list' % model_name)
        response = self.client.get(list_url)

        if not can_access:
            self.assertEquals(response.status_code, 403)
            return

        self.assertContains(response, '>{}</p>'.format(user_name),
                            msg_prefix='user name should be in the top menu' + info)

        self.assertContains(response, 'List (',
                            msg_prefix='table item count should be visible' + info)

        model_name_plural = model_name + ('' if model_name == 'news' else 's')
        crawl_button_text = '>Crawl %s Now</button>' % model_name_plural.title()
        if can_crawl is True:
            self.assertContains(response, crawl_button_text,
                                msg_prefix='crawl button should be present' + info)
        elif can_crawl is False:
            self.assertNotContains(response, crawl_button_text,
                                   msg_prefix='crawl button should not be present' + info)
