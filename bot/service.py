import os
import sys
import re
import logging
from datetime import time, datetime
from time import sleep
from .api import api_request
from .news import NewsSpider
from .tips import TipsSpider


DEFAULT_POLL_SECONDS = 50


def run_action(action, env={}):
    spider_cls = dict(news=NewsSpider, tips=TipsSpider)[action]
    final_env = os.environ.copy()
    final_env.update(env)
    spider = spider_cls(final_env)
    try:
        spider.run()
    finally:
        spider.close()


class Schedule(object):
    default_schedule = {
        time(11, 02): 'tips',
        time(11, 46): 'tips',
        time(12, 02): 'tips',
        time(10, 00): 'news',
        time(18, 30): 'news',
    }

    def __init__(self):
        self.last_mtime = self.mtime
        self.reset_nightly = True
        self.load()

    def take_action(self):
        now = datetime.now().replace(microsecond=0)
        for t in sorted(self.pendingrun):
            if now.time() >= t:
                action = self.pendingrun[t]
                del self.pendingrun[t]
                return action, now
        return None, now

    def reload(self):
        new_mtime = self.mtime
        if new_mtime != self.last_mtime:
            self.last_mtime = new_mtime
            self.load()

    def nightly(self):
        now = datetime.now().replace(microsecond=0)
        if now.hour == 0:
            if self.reset_nightly:
                self.reset_nightly = False
                for t in self.schedule:
                    self.pendingrun[t] = self.schedule[t]
        else:
            self.reset_nightly = True

    def load(self):
        try:
            self.parse()
            print 'Using schedule from %s' % self.filename
            print 'New schedule: %s' % self
        except (IOError, OSError, AssertionError) as error:
            print 'Failed to read schedule %s: %s' % (self.filename, error)
            self.schedule = self.default_schedule.copy()
            print 'Using default schedule: %s' % self

        now = datetime.now().replace(microsecond=0)
        self.pendingrun = {}
        for t in self.schedule:
            if t > now.time():
                self.pendingrun[t] = self.schedule[t]

    def parse(self):
        schedule = {}
        for n, line in enumerate(open(self.filename, 'rb'), start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            mo = re.match('(\d\d?):(\d\d)\s+(news|tips)', line)
            assert mo, 'Syntax error in line %d, must be HH:MM news/tips' % n
            schedule[time(int(mo.group(1)), int(mo.group(2)))] = mo.group(3)
        self.schedule = schedule

    @property
    def filename(self):
        from vanko.scrapy import DEFAULT_PROJECT_DIR
        from .spider import BOT_NAME

        path = os.path.join(DEFAULT_PROJECT_DIR, BOT_NAME, 'schedule.txt')
        return os.path.abspath(path)

    @property
    def mtime(self):
        try:
            return os.stat(self.filename).st_mtime
        except (IOError, OSError):
            return 0

    def __str__(self):
        a = ['%02d:%02d %s' % (tm.hour, tm.minute, job)
             for tm, job in sorted(self.schedule.items())]
        return '[%s]' % ', '.join(a)


class Service(object):
    def __init__(self, setup_logging=False):
        self.logger = None
        if setup_logging:
            logging.basicConfig(
                format='%(asctime)s (%(process)d) [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                stream=sys.stdout, level=logging.INFO)
            self.logger = logging.getLogger('dvoznak_service')
        self.schedule = Schedule()

    def run(self):
        print 'Service running'
        while 1:
            poll_seconds = int(os.environ.get('POLL_SECONDS', DEFAULT_POLL_SECONDS))
            sleep(poll_seconds)
            try:
                self.loop()
            except Exception as err:
                print 'Service caught %r' % err

    def loop(self):
        self.schedule.reload()
        self.schedule.nightly()
        action, starttime = self.schedule.take_action()
        if action:
            print 'Scheduled crawl for {} at {}'.format(action, starttime)
            res = api_request(logger=self.logger, action=action, type='auto',
                              starttime=starttime, request='run')
            env = res.get('env', {})
            return run_action(action, env)

        res = api_request(logger=self.logger, action='service', type='manual', request='run')
        if res:
            action = res.get('action', None)
            env = res.get('env', {})
            self.last_env = env.copy()
            if action:
                return run_action(action, env)
