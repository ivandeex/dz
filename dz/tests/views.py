
class ListViewTestsMixin(object):
    def test_admin_users_can_access_all_tables(self):
        for username in ('super', 'follow'):
            with self.login_as(username):
                for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
                    self._test_table_view(username, model_name, can_access=True)

    def test_admin_users_can_crawl_news_and_tips(self):
        for username in ('super', 'follow'):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_crawl=True)

    def test_admin_users_can_delete_rows_in_tables(self):
        for username in ('super', 'follow'):
            with self.login_as(username):
                for model_name in ('news', 'tip', 'crawl', 'user', 'schedule'):
                    self._test_table_view(username, model_name, can_use_row_actions=True)

    def test_admin_users_can_export_news_and_tips(self):
        for username in ('super', 'follow'):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_export=True)

    def test_admin_users_cannot_export_other_models(self):
        for username in ('super', 'follow'):
            with self.login_as(username):
                for model_name in ('crawl', 'user', 'schedule'):
                    self._test_table_view(username, model_name, can_export=False)

    def test_simple_users_can_export_news_and_tips(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_export=True)

    def test_simple_users_cannot_crawl_news_and_tips(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_crawl=False)

    def test_simple_users_cannot_delete_news_and_tips(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_use_row_actions=False)

    def test_simple_users_cannot_access_privileged_tables(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('crawl', 'user', 'schedule'):
                    self._test_table_view(username, model_name, can_access=False)

    def _page_should_load_custom_js_css(self, response, info, target, skin):
        msg = 'the page must load custom js/css' + info

        for bundle in ('common', skin):
            if target == 'prod':
                bundle += '.min'

            link_css = ('<link type="text/css" href="/static/%s/dz-%s.css?hash='
                        % (target, bundle))
            self.assertContains(response, link_css, msg_prefix=msg)

            link_js = ('<script type="text/javascript" src="/static/%s/dz-%s.js?hash='
                       % (target, bundle))
            self.assertContains(response, link_js, msg_prefix=msg)
