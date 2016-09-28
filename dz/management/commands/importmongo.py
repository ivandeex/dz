import sys
import pytz
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient
from dz import models
from dz.config import spider_config


class Command(BaseCommand):
    help = 'Migrates MongoDB data to Django database'

    DEFAULT_SCHEDULE = [
        (time(11, 02), 'tips'),
        (time(11, 46), 'tips'),
        (time(12, 02), 'tips'),
        (time(10, 00), 'news'),
        (time(18, 30), 'news'),
    ]

    def convert_time(self, dt):
        if dt:
            if not isinstance(dt, datetime):
                dt = timezone.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            if not timezone.is_aware(dt):
                dt = self.default_tz.localize(dt)
            return dt.astimezone(timezone.utc)

    def add_arguments(self, parser):
        parser.add_argument(
            '--table', '-t', dest='table', help='Table to import',
            default='all', choices=['all', 'schedule', 'users', 'crawls', 'tips', 'news']
        )

        parser.add_argument(
            '--url', '-u', dest='mongourl', default=settings.MONGODB_URL, help='MongoDB URL'
        )

    def handle(self, *args, **options):
        self.default_tz = pytz.timezone(spider_config('TIME_ZONE'))
        self.mongodb = MongoClient(options['mongourl']).get_default_database()

        table = options['table']

        if table in ('schedule', 'all'):
            self.import_schedule()
        if table in ('users', 'all'):
            self.import_users()
        if table in ('crawls', 'all'):
            self.import_crawls()
        if table in ('tips', 'all'):
            self.import_tips()
        if table in ('news', 'all'):
            self.import_news()

        self.mongodb.client.close()

    def import_schedule(self):
        models.Schedule._verbose_update = False
        models.Schedule.objects.all().delete()
        for time_i, target_i in self.DEFAULT_SCHEDULE:
            models.Schedule.objects.create(time=time_i, target=target_i)
        print '%d schedule jobs imported' % len(self.DEFAULT_SCHEDULE)

    def import_users(self):
        models.User.objects.all().delete()
        count = 0
        for item in self.mongodb.dvoznak_users.find(sort=[('username', 1)]):
            models.User.objects.create(
                username=item['username'],
                password=item['password'],
                is_admin=item['is_admin'],
            )
            count += 1
        print '%d users imported' % count

    def import_crawls(self):
        models.Crawl.objects.all().delete()
        count = 0

        ordering = [('pk', 1)]
        self.mongodb.dvoznak_crawls.create_index(ordering)
        for item in self.mongodb.dvoznak_crawls.find(sort=ordering):
            if item['status'] == 'finished':
                item['status'] = 'complete'
            models.Crawl.objects.create(
                pk=item['pk'],
                target=item['action'],
                manual=item['type'] == 'manual',
                status=item['status'],
                started=self.convert_time(item['started']),
                ended=self.convert_time(item.get('ended')),
                count=item['news' if item['action'] == 'news' else 'tips'] or 0,
                host=item['host'] or item['ipaddr'] or '-',
                pid=item['pid'] or 0,
            )
            count += 1
        print '%d crawls imported' % count

    def import_tips(self):
        models.Tip.objects.all().delete()
        count = 0

        ordering = [('published', 1), ('crawled', 1)]
        self.mongodb.dvoznak_tips.create_index(ordering)
        for item in self.mongodb.dvoznak_tips.find(sort=ordering):
            published = self.convert_time(item['published'])
            updated = self.convert_time(item['updated'])
            crawled = self.convert_time(item['crawled'])

            models.Tip.objects.create(
                pk=item['pk'],
                league=item['place'],
                parties=item['title'],
                title=item['tip'],
                text=item.get('text'),
                bookmaker=item['betting'],
                odds=item['coeff'],
                min_odds=item['min_coeff'],
                result=item['result'],
                earnings=item['due'],
                spread=item['spread'],
                stake=item['stake'],
                success=item['success'],
                tipster=item['tipster'],
                published=published or updated,
                updated=updated,
                crawled=crawled,
                link=item['details_url'],
                archived=item['archived'] != 'fresh',
            )
            count += 1
        print '%d tips imported' % count

    def import_news(self):
        print 'imporing news...'
        models.News.objects.all().delete()
        count = 0

        ordering = [('published', 1), ('crawled', 1)]
        self.mongodb.dvoznak_news.create_index(ordering)
        for item in self.mongodb.dvoznak_news.find(sort=ordering):
            if count % 100 == 0:
                print >>sys.stderr, '%d.. ' % count,

            item.setdefault('preamble', '')
            item.setdefault('content', '')

            published = self.convert_time(item.get('published'))
            updated = self.convert_time(item['updated'])
            crawled = self.convert_time(item['crawled'])

            archived = item['archived'] != 'fresh'

            models.News.objects.create(
                id=item['pk'],
                link=item['url'],
                title=item['title'],
                sport=item['section'],
                league=item['subsection'],
                parties=item['short_title'],
                published=published or updated,
                updated=updated,
                crawled=crawled,
                archived=archived,
            )

            models.NewsText.objects.create(
                news_id=item['pk'],
                preamble=item['preamble'],
                content=item['content'],
                datatable=item['subtable'],
            )

            count += 1

        if count:
            print >>sys.stderr, ''
        print '%d news imported' % count
