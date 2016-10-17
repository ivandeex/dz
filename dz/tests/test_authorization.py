from django.test import tag
from . import base
from .base import get_pass


@tag('basic')
class DzLoginTestCase(base.BaseDzTestCase):
    def test_admin_user_should_not_login(self):
        # Should not login because dz's User model never overrides admin password
        self.assertFalse(
            self.client.login(username='admin', password=get_pass('admin')),
            'should not login as admin user'
        )

    def test_non_admin_user_should_login(self):
        for username in ('super', 'follow', 'simple'):
            self.assertTrue(
                self.client.login(username=username, password=get_pass(username)),
                'should login as test user %s' % username
            )
            self.client.logout()
