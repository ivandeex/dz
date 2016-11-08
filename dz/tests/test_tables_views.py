import random
from parsel import Selector
from urllib import urlencode
from django.test import tag
from django.urls import reverse
from dz import models
from . import base, views


@tag('views')
class TableViewsTests(base.BaseDzTestCase, views.ListViewTestsMixin):
    MODEL_TABLE_SIZES = {
        'news': base.MODEL_BATCH_SIZE,  # created from factory batch
        'tip': base.MODEL_BATCH_SIZE,  # created from factory batch
        'crawl': base.MODEL_BATCH_SIZE,  # created from factory batch
        'user': len(base.TEST_USERS),  # created from hardcoded list
        'schedule': base.SCHEDULE_FIXTURE_LENGTH,  # created from fixture "schedule.json"
    }

    def test_unauthorized_request_should_redirect_to_login(self):
        for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
            list_url = reverse('dz:%s-list' % model_name)
            login_url = '%s?next=%s' % (reverse('dz-admin:login'), list_url)
            response = self.client.get(list_url)
            self.assertRedirects(response, login_url)

    def _test_table_view(self, user_name, model_name,
                         can_access=True, can_crawl=None,
                         can_use_row_actions=None):
        info = ' (user: {}, model: {})'.format(user_name, model_name)
        list_url = reverse('dz:%s-list' % model_name)
        response = self.client.get(list_url + '?flt-archived=all')

        if not can_access:
            self.assertEquals(response.status_code, 403)
            return

        self.assertContains(response, '>{}</p>'.format(user_name),
                            msg_prefix='user name should be in the top menu' + info)

        expected_text = 'List (%d)' % self.MODEL_TABLE_SIZES[model_name]
        self.assertContains(response, expected_text,
                            msg_prefix='table item count should be visible' + info)

        model_name_plural = model_name + ('' if model_name == 'news' else 's')
        crawl_button_text = '>Crawl %s Now</button>' % model_name_plural.title()
        if can_crawl is True:
            self.assertContains(response, crawl_button_text,
                                msg_prefix='crawl button should be present' + info)
        if can_crawl is False:
            self.assertNotContains(response, crawl_button_text,
                                   msg_prefix='crawl button should not be present' + info)

        row_selector_text = '<th class="col-row_selector">'
        row_actions_text = '<th class="col-row_actions">'
        if can_use_row_actions is True:
            self.assertContains(response, row_selector_text,
                                msg_prefix='row selector should be present' + info)
            self.assertContains(response, row_actions_text,
                                msg_prefix='row actions should be present' + info)
        if can_use_row_actions is False:
            self.assertNotContains(response, row_selector_text,
                                   msg_prefix='row selector should be hidden' + info)
            self.assertNotContains(response, row_actions_text,
                                   msg_prefix='row actions should be hidden' + info)


@tag('actions')
class RowActionFormTests(base.BaseDzTestCase):
    def test_simple_users_cannot_delete(self):
        with self.login_as('simple'):
            form_url = reverse('dz:row-action')

            for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
                data = dict(model_name=model_name, action='delete', row_ids='1')
                response = self.client.post(form_url, data)
                self.assertEquals(response.status_code, 403)

    def test_row_action_form_can_detect_invalid_parameters(self):
        msg_base = 'Row action form should detect '
        form_url = reverse('dz:row-action')

        def assertFails(params, description):
            response = self.client.post(form_url, params)
            self.assertEquals(response.status_code, 400, msg=msg_base + description)

        with self.login_as('super'):
            request = self.client.get(form_url)
            self.assertEquals(request.status_code, 405,
                              msg=msg_base + 'GET request')
            assertFails({},
                        'empty post')
            assertFails(dict(model_name='trump', action='delete', row_ids='1'),
                        'invalid model')
            assertFails(dict(model_name='news', action='', row_ids='1'),
                        'empty action')
            assertFails(dict(model_name='news', action='trump', row_ids='1'),
                        'invalid action')
            assertFails(dict(model_name='news', action='delete', row_ids=''),
                        'empty ids')
            assertFails(dict(model_name='news', action='delete', row_ids='1,X'),
                        'invalid ids')

    @models.Schedule.suspend_logging
    def test_admin_users_can_delete(self):
        with self.login_as('super'):
            form_url = reverse('dz:row-action')

            for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
                ModelClass = getattr(models, model_name.title())
                list_url = reverse('dz:%s-list' % model_name)
                count_before = ModelClass.objects.count()

                if model_name == 'user':
                    # Don't remove current user, else the current login session would break.
                    queryset = ModelClass.objects.filter(username__in=['admin', 'simple'])
                else:
                    queryset = ModelClass.objects.all()
                del_ids = sorted(queryset.values_list('pk', flat=True))[:2]

                msg = '{} action form should redirect to {}'.format(model_name, list_url)
                data = {
                    'model_name': model_name,
                    'action': 'delete',
                    'row_ids': '%d,%d' % tuple(del_ids)
                }
                response = self.client.post(form_url, data)
                self.assertRedirects(response, list_url, msg_prefix=msg)

                msg = '{:d} {} objects should be deleted'.format(len(del_ids), model_name)
                count_after = ModelClass.objects.count()
                self.assertEquals(count_after, count_before - len(del_ids), msg=msg)


@tag('filters')
class TableFiltersTests(base.BaseDzTestCase):
    def get_parsed_html(self, url=None, query=None, username='super'):
        self.client.login(username=username, password=base.get_pass(username))
        if url is None:
            url = reverse('dz:user-list')
        if query is not None and query != '':
            url += '?' + urlencode(query)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        text = response.content.decode(response.charset)
        select = Selector(text)
        return select

    def test_the_filter_word_is_not_among_filter_form_help_strings(self):
        select = self.get_parsed_html(query='')
        help_blocks = select.css('#dz-filter-block .help-block::text')
        help_strings = set(text.strip() for text in help_blocks.extract())
        self.assertNotIn('Filter', help_strings)

    def test_filter_reset_button_must_be_disabled_without_query(self):
        select = self.get_parsed_html(query='')
        reset_button = select.css('#dz-filter-block button:contains("Reset")')
        self.assertEquals(len(reset_button.extract()), 1)
        disabled = reset_button.css('::attr(disabled)').extract_first()
        self.assertEquals(disabled, 'disabled')

    def test_filter_reset_button_must_be_enabled_when_there_is_query(self):
        select = self.get_parsed_html(query={'flt-can_follow': 1})
        reset_button = select.css('#dz-filter-block button:contains("Reset")')
        self.assertEquals(len(reset_button.extract()), 1)
        disabled = reset_button.css('::attr(disabled)').extract_first()
        self.assertIsNone(disabled)

    def test_filter_button_must_be_white_if_filter_is_identity(self):
        query1 = ''
        query2 = {'flt-is_admin': 1, 'flt-can_follow': 1}
        for query in (query1, query2):
            select = self.get_parsed_html(query=query)
            button = select.css('.table-tools button:contains("Filters")')
            self.assertEquals(len(button.extract()), 1)
            classes = button.css('::attr(class)').extract_first().split()
            self.assertIn('btn-default', classes)
            self.assertNotIn('btn-primary', classes)

    def test_filter_button_must_be_blue_if_filter_is_effective(self):
        for admin_choice in (2, 3):
            for follow_choice in (2, 3):
                query = {'flt-is_admin': admin_choice, 'flt-can_follow': follow_choice}
                select = self.get_parsed_html(query=query)
                button = select.css('.table-tools button:contains("Filters")')
                self.assertEquals(len(button.extract()), 1)
                classes = button.css('::attr(class)').extract_first().split()
                self.assertNotIn('btn-default', classes)
                self.assertIn('btn-primary', classes)


@tag('forms')
class TableFormTests(base.BaseDzTestCase):
    def get_random_pk(self, model_name):
        ModelClass = getattr(models, model_name.title())
        pk_list = ModelClass.objects.values_list('pk', flat=True)
        return random.choice(pk_list)

    def get_random_form_url(self, model_name, pk=None):
        if pk is None:
            pk = self.get_random_pk(model_name)
        return reverse('dz:%s-form' % model_name, kwargs={'pk': pk})

    def test_unauthorized_request_should_redirect_to_login(self):
        for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
            form_url = self.get_random_form_url(model_name)
            login_url = '%s?next=%s' % (reverse('dz-admin:login'), form_url)
            response = self.client.get(form_url)
            self.assertRedirects(response, login_url)

    def test_simple_user_cannot_access_elevated_forms(self):
        with self.login_as('simple'):
            for model_name in ('crawl', 'user', 'schedule'):
                form_url = self.get_random_form_url(model_name)
                response = self.client.get(form_url)
                self.assertEquals(response.status_code, 403)

    def test_simple_user_cannot_post_simple_forms(self):
        with self.login_as('simple'):
            for model_name in ('news', 'tip'):
                pk = self.get_random_pk(model_name)
                form_url = self.get_random_form_url(model_name, pk)
                response = self.client.get(form_url)
                self.assertEquals(response.status_code, 200)
                response = self.client.post(form_url, {'id': pk})
                self.assertEquals(response.status_code, 403)

    def test_admin_user_can_post_all_forms(self):
        with self.login_as('super'):
            for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
                pk = self.get_random_pk(model_name)
                form_url = self.get_random_form_url(model_name, pk)
                response = self.client.get(form_url)
                self.assertEquals(response.status_code, 200)
                response = self.client.post(form_url, {'id': pk})
                self.assertEquals(response.status_code, 200)
                self.assertContains(response, '<div class="form-group has-error">')
