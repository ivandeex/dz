
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

    def test_simple_users_cannot_crawl_news_and_tips(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('news', 'tip'):
                    self._test_table_view(username, model_name, can_crawl=False)

    def test_simple_users_cannot_access_privileged_tables(self):
        for username in ('simple',):
            with self.login_as(username):
                for model_name in ('crawl', 'user', 'schedule'):
                    self._test_table_view(username, model_name, can_access=False)
