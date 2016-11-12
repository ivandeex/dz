import sys
from django.core.management.base import BaseCommand
from django.db.models import Q
from dz import models


class Command(BaseCommand):  # pragma: no cover
    help = 'Upgrade data in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', '-t', dest='target', help='Target to upgrade',
            default='all', choices=['all', 'users', 'league', 'links']
        )

    def handle(self, *args, **options):
        target = options['target']

        if target in ('all', 'users'):
            self.upgrade_users()
        if target in ('all', 'league'):
            self.upgrade_news_league()
        if target in ('all', 'links'):
            self.upgrade_news_links()

        print 'OK'

    def upgrade_users(self):
        print 'upgrade user permissions...'
        for user in models.User.objects.all():
            user.save()

    def upgrade_news_league(self):
        print 'upgrading news leagues...'
        count = 0

        for news in models.News.objects.filter(league__contains=',').only('league'):
            news.save()  # upgrade is performed by News.save()
            count += 1

        if count:
            print '%d leagues upgraded' % count

    def upgrade_news_links(self):
        print 'upgrading news links...'
        newstext_mgr = models.NewsText.objects
        count = 0

        # These regular expressions are taken from NewsText.save()
        # with \b removed, because postgres does not understand it;
        # the ending part is unimportant and also removed.
        link_regex = r'(<a|&lt;a)\s[^>]*?href="[^#][^"]+"'
        bookmaker_img_regex = r'<img\s[^>]*?src="img/kladionice/[^/"]+"'

        work_set = newstext_mgr.filter(
            Q(content__regex=link_regex) |
            Q(datatable__regex=link_regex) |
            Q(datatable__regex=bookmaker_img_regex)
        )

        # keep memory low: create list of ids, then load items one-by-one
        for pk in sorted(work_set.values_list('pk', flat=True)):
            if count % 100 == 0:
                print >>sys.stderr, '%d.. ' % count,
            newstext_mgr.get(pk=pk).save()  # upgrade is performed by NewsText.save()
            count += 1

        if count:
            print '\n%d news links upgraded' % count
