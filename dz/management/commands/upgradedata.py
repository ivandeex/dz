import sys
from django.core.management.base import BaseCommand
from django.db.models import Q
from dz import models


class Command(BaseCommand):
    help = 'Upgrade data in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', '-t', dest='target', help='Target to upgrade',
            default='all', choices=['all', 'users', 'news']
        )

    def handle(self, *args, **options):
        target = options['target']

        if target in ('all', 'users'):
            self.upgrade_users()
        if target in ('all', 'news'):
            self.upgrade_news()

        print 'OK'

    def upgrade_users(self):
        print 'upgrade user permissions...'
        for user in models.User.objects.all():
            user.save()

    def upgrade_news(self):
        print 'upgrading news...'
        news_mgr = models.News.objects
        count = 0

        # These regular expressions are taken from News.save()
        # with \b removed, because postgres does not understand it;
        # the ending part is unimportant and also removed.
        link_regex = r'(<a|&lt;a)\s[^>]*?href="[^#][^"]+"'
        bookmaker_img_regex = r'<img\s[^>]*?src="img/kladionice/[^/"]+"'

        work_set = news_mgr.filter(
            Q(content__regex=link_regex) |
            Q(subtable__regex=link_regex) |
            Q(subtable__regex=bookmaker_img_regex) |
            Q(league__contains=',')
        )

        # keep memory low: create list of ids, then load items one-by-one
        for pk in sorted(work_set.values_list('pk', flat=True)):
            if count % 100 == 0:
                print >>sys.stderr, '%d.. ' % count,
            news_mgr.get(pk=pk).save()  # upgrade is performed by overridden save()
            count += 1

        if count:
            print '\n%d news upgraded' % count
