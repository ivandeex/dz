import os
import re
from datetime import time, datetime
from time import sleep
from .utils import logger, get_project_dir
from .api import api_request
from .news import NewsSpider
from .tips import TipsSpider


DEFAULT_POLL_SECONDS = 50


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
            logger.info('Using schedule from %s', self.filename)
            logger.info('New schedule: %s', self)
        except (IOError, OSError, AssertionError) as error:
            logger.error('Failed to read schedule %s: %s', self.filename, error)
            self.schedule = self.default_schedule.copy()
            logger.info('Using default schedule: %s', self)

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
        path = os.path.join(get_project_dir(), 'dvoznak', 'schedule.txt')
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
    def __init__(self):
        self.schedule = Schedule()

    def run(self):
        logger.info('Service running')
        while 1:
            poll_seconds = int(os.environ.get('POLL_SECONDS', DEFAULT_POLL_SECONDS))
            sleep(poll_seconds)
            try:
                self.loop()
            except Exception as err:
                logger.error('Service error: %r', err)

    def loop(self):
        self.schedule.reload()
        self.schedule.nightly()
        action, starttime = self.schedule.take_action()
        if action:
            logger.info('Scheduled crawl for %s at %s', action, starttime)
            res = api_request(action=action, type='auto', starttime=starttime, request='run')
            return self.action(action, res.get('env', {}))

        res = api_request(action='service', type='manual', request='run')
        if res:
            action = res.get('action', None)
            self.last_env = res.get('env', {})
            if action:
                return self.action(action, self.last_env)

    @staticmethod
    def action(action, env={}):
        spider_cls = dict(news=NewsSpider, tips=TipsSpider)[action]
        environ = os.environ.copy()
        environ.update(env)
        spider = spider_cls(environ)
        try:
            spider.run()
        finally:
            spider.close()
