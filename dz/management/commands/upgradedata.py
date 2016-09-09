import sys
from django.core.management.base import BaseCommand
from django.db.models import Q
from dz import models


class Command(BaseCommand):
    help = 'Upgrade data in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', '-t', dest='target', help='Target to upgrade',
            default='all', choices=['all', 'users', 'league', 'nolinks']
        )

    def handle(self, *args, **options):
        target = options['target']

        if target in ('all', 'users'):
            self.upgrade_users()
        if target in ('all', 'league'):
            self.upgrade_league()
        if target in ('all', 'nolinks'):
            self.deactivate_news_links()

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

    def deactivate_news_links(self):
        print 'hide links in news...'
        count = 0
        news_mgr = models.News.objects
        # This is regular expression from News.save().deactivate_links(),
        # but with \b removed, because postgres does not understand it;
        # the ending part is unimportant and also removed.
        regex = r'(<a|&lt;a)\s([^>]*?)href="([^#][^"]+)"'
        workset = news_mgr.filter(Q(content__regex=regex) | Q(subtable__regex=regex))
        for news in workset.only('content', 'subtable'):
            if count % 100 == 0:
                print >>sys.stderr, '%d.. ' % count,
            # hiding is performed by overridden save() method
            news.save()
            count += 1
        if count:
            print '\n%d links deactivated' % count
