from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient
from dz import models


class Command(BaseCommand):
    help = 'Migrates MongoDB data into Postgres'

    @staticmethod
    def convert_datetime(dt):
        if dt:
            if isinstance(dt, basestring):
                dt = timezone.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            return timezone.make_aware(dt)

    def add_arguments(self, parser):
        parser.add_argument(
            '--table', '-t', dest='table', help='Table(s) to import',
            default='all', choices=['all', 'users', 'crawls', 'tips', 'news']
        )

    def handle(self, *args, **options):
        table = options['table']
        self.mongodb = MongoClient(settings.MONGODB_URL).get_default_database()
        if table in ('users', 'all'):
            count = self.import_users()
            print '%d users imported' % count
        if table in ('crawls', 'all'):
            count = self.import_crawls()
            print '%d crawls imported' % count
        if table in ('tips', 'all'):
            count = self.import_tips()
            print '%d tips imported' % count
        if table in ('news', 'all'):
            count = self.import_news()
            print '%d news imported' % count
        self.mongodb.client.close()

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
        return count

    def import_crawls(self):
        models.Crawl.objects.all().delete()
        count = 0
        ordering = [('pk', 1)]
        self.mongodb.dvoznak_crawls.create_index(ordering)
        for item in self.mongodb.dvoznak_crawls.find(sort=ordering):
            models.Crawl.objects.create(
                id=item['pk'],
                type=item['type'],
                action=item['action'],
                status=item['status'],
                started=self.convert_datetime(item['started']),
                ended=self.convert_datetime(item.get('ended')),
                news=item['news'],
                tips=item['tips'],
                host=item['host'],
                ipaddr=item['ipaddr'],
                pid=item['pid'],
            )
            count += 1
        return count

    def import_tips(self):
        models.Tip.objects.all().delete()
        ordering = [('published', 1), ('crawled', 1)]
        self.mongodb.dvoznak_tips.create_index(ordering)
        count = 0
        for item in self.mongodb.dvoznak_tips.find(sort=ordering):
            models.Tip.objects.create(
                id=item['pk'],
                title=item['title'],
                place=item['place'],
                tip=item['tip'],
                text=item.get('text'),
                betting=item['betting'],
                coeff=item['coeff'],
                min_coeff=item['min_coeff'],
                result=item['result'],
                due=item['due'],
                spread=item['spread'],
                stake=item['stake'],
                success=item['success'],
                tipster=item['tipster'],
                published=self.convert_datetime(item['published']),
                updated=self.convert_datetime(item['updated']),
                crawled=self.convert_datetime(item['crawled']),
                details_url=item['details_url'],
                archived=item['archived'],
            )
            count += 1
        return count

    def import_news(self):
        models.News.objects.all().delete()
        ordering = [('published', 1), ('crawled', 1)]
        self.mongodb.dvoznak_news.create_index(ordering)
        count = 0
        for item in self.mongodb.dvoznak_news.find(sort=ordering):
            if 'published' not in item:
                item['published'] = item['updated']
            item.setdefault('preamble', '')
            item.setdefault('content', '')
            models.News.objects.create(
                id=item['pk'],
                url=item['url'],
                title=item['title'],
                short_title=item['short_title'],
                section=item['section'],
                subsection=item['subsection'],
                published=self.convert_datetime(item['published']),
                updated=self.convert_datetime(item['updated']),
                crawled=self.convert_datetime(item['crawled']),
                archived=item['archived'],
                preamble=item['preamble'],
                content=item['content'],
                subtable=item['subtable'],
            )
            count += 1
        return count
