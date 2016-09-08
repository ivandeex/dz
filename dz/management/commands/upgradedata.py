from django.core.management.base import BaseCommand
from dz import models


class Command(BaseCommand):
    help = 'Upgrade data in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', '-t', dest='target', help='Target to upgrade',
            default='all', choices=['all', 'users', 'league']
        )

    def handle(self, *args, **options):
        target = options['target']

        if target in ('all', 'users'):
            self.upgrade_users()
        if target in ('all', 'league'):
            self.upgrade_league()

        print 'OK'

    def upgrade_users(self):
        print 'upgrade user permissions...'
        for user in models.User.objects.all():
            user.save()

    def upgrade_league(self):
        print 'remove comma from league...'
        count = 0
        for news in models.News.objects.filter(league__contains=',').only('id', 'league'):
            news.league = news.league.partition(',')[0]
            news.save()
            count += 1
        if count:
            print '%d commas removed' % count
