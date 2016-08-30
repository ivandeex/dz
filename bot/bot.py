#!/usr/bin/env python
import os
import sys
import re
import logging
import mimetypes
import hashlib
import random
import requests
import socket

from multiprocessing import freeze_support
from datetime import datetime, time
from time import sleep
from urlparse import urljoin
from scrapy.loader.processors import Identity
from selenium.webdriver.common.by import By


_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_parent_dir)


if True:
    from vanko.scrapy import (
        CustomSettings, CustomSpider,
        setup_spider, run_spider, DEFAULT_PROJECT_DIR,
        TakeFirstItemLoader, Item, Field,
        StripField, JoinField, DateTimeField)
    from vanko.utils import (
        getenv, decode_userpass, randsleep, as_list, extract_datetime)
    from vanko.scrapy.webdriver import WebdriverRequest, WebdriverResponse
    # from vanko.utils.pdb import set_trace


setup_spider(__name__)
BOT_NAME = 'dvoznak'
logger = logging.getLogger(BOT_NAME)

CustomSettings.register(
    NEWS_TO_SKIP='',
    USERPASS='',
    STORAGE='normal',
    HTTPCACHE_EXPIRATION_SECS=600,
    DOWNLOAD_DELAY=40,
    AUTOTHROTTLE_START_DELAY=80,
    AUTOTHROTTLE_ENABLED=True,
    WEBDRIVER_BROWSER='phantomjs',
    MAX_NEWS=0,
    SINGLE_PK=0,
    WITH_IMAGES=True,
    STARTTIME='',
)

POLL_SECONDS = getenv('POLL_SECONDS', 50)
WEB_SERVER = getenv('WEB_SERVER', 'http://dz.more.vanko.me/dz/api/spider/')
SECRET_KEY = getenv('SECRET_KEY', 'kLIuJ_dvoznak2016_v4')


class NewsItem(Item):
    pk = Field()
    url = Field()
    crawled = Field()
    section = StripField()
    subsection = StripField()
    updated = DateTimeField(fix=True, dayfirst=True)
    short_title = StripField()
    title = StripField()
    published = DateTimeField(fix=True, dayfirst=True)
    preamble = StripField()
    content = JoinField(strip=True, sep='\n')
    subtable = JoinField(strip=True, sep='\n')
    subtable2 = JoinField(strip=True, sep='\n')
    image1_filename = Field()
    image1_mimetype = Field()
    image1_base64data = Field()
    # Temporary fields:
    image_urls = Field(output_processor=Identity())
    images = Field()


class TipsItem(Item):
    pk = Field()
    place = StripField()
    title = StripField()
    tip = StripField()
    published = DateTimeField(fix=True, dayfirst=True)
    updated = DateTimeField(fix=True, dayfirst=True)
    text = JoinField(sep=' ')
    result = Field()
    tipster = Field()
    coeff = Field()
    min_coeff = Field()
    stake = Field()
    due = Field()
    spread = Field()
    betting = Field()
    success = Field()
    details_url = Field()
    crawled = Field()


class DvoznakSpider(CustomSpider):

    name = BOT_NAME
    allowed_domains = ['dvoznak.com']
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36'
    login_pending = True
    homepage = 'http://www.dvoznak.com/'

    def __init__(self, *args, **kwargs):
        s = self.settings_init
        self.username, self.password = decode_userpass(s.get('USERPASS'))
        self.starttime = s.get('STARTTIME') or \
            str(datetime.utcnow().replace(microsecond=0))
        self.delay_base = s.getint('DOWNLOAD_DELAY', 40)
        self.max_news = s.getint('MAX_NEWS', 0)
        self.single_pk = s.getint('SINGLE_PK', 0)
        self.with_images = s.getbool('WITH_IMAGES', True)

        self.seen = []
        seen = s.get('NEWS_TO_SKIP', '').strip()
        if seen:
            self.seen = set([int(x.strip()) for x in seen.split(',')])

        self.news = []
        self.tips = []
        self.crawled = set()
        self.skipped = set()
        self.numinfo = True
        self.tocrawl = 0
        self.ercount = 0

    def start_requests(self):
        yield WebdriverRequest(
            self.homepage, callback=self.wd_start,
            dont_filter=True, meta=dict(dont_cache=True))

    def wd_start(self, response):
        assert isinstance(response, WebdriverResponse)
        result = []
        if 'tips' in self.action_list:
            self.wd_login(response)
            self.wd_click_menu(response, 'Prognoze')
            self.tips_list(response)
        elif 'news' in self.action_list:
            result = self.wd_news_safe(response)
        for x in as_list(result):
            yield x

    def wd_login(self, response):
        response.wait_for_ajax()
        randsleep(2)
        if not (self.username and self.password):
            self.logger.info('Working without login (browser)')
            return
        form_name = 'prijava'
        form = response.css('form[name="%s"]' % form_name)
        id_user = form.css(
            'input[type="text"]::attr(id)').extract_first()
        id_pass = form.css(
            'input[type="password"]::attr(id)').extract_first()

        self.logger.debug('Opening login drawer')
        response.click_safe('login_btn')
        response.wait_for_ajax()
        randsleep(2)
        self.logger.debug('Filling the form')
        response.send_keys_safe(id_user, self.username)
        response.send_keys_safe(id_pass, self.password)
        randsleep(2)
        self.logger.debug('Click the login button')
        response.click_safe('Prijava', by=By.NAME)
        randsleep(4)
        self.logger.info('Logged in as %s (browser)', self.username)

    def wd_click_menu(self, response, menu):
        self.logger.debug('Searching for %s menu', menu)
        el = response.webdriver.find_element_by_xpath(
            '//ul[@id="mainmenu"]/li/a[contains(.,"%s")]' % menu)
        self.logger.debug('Clicking on %s menu', menu)
        el.click()
        self.logger.debug('Waiting for menu ajax to finish')
        response.wait_for_ajax()
        self.logger.debug('Safety delay after click')
        randsleep(4)

    # ############### TIPS ################

    def on_tips(self):
        self.clear_cache('all')
        self.logger.info('Crawling tips')

    def tips_list(self, response):
        tiplist = response.wait_css('.tiprog_list_block')
        for tip in tiplist:
            item = self.parse_tip(tip, response)
            if item:
                self.tips.append(item)

    def parse_tip(self, tip, response):
        ldr = TakeFirstItemLoader(TipsItem(), tip)
        details_url = response.urljoin(
            tip.css('.tpl_right > h3 > a ::attr(href)').extract_first())
        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', details_url).group(1))
        except Exception:
            self.logger.info('Skipping tip %s', details_url)
            return
        ldr.add_value('pk', pk)
        ldr.add_value('details_url', details_url)
        ldr.add_value('crawled', datetime.utcnow().replace(microsecond=0))

        ldr.add_css('place', '.tpl_right > h3 > span ::text')
        ldr.add_css('title', '.tpl_right > h3 > a ::text')
        ldr.add_css('tip', '.tiprot_left > strong ::text')
        ldr.add_css('updated', '.tiprot_right ::text')
        all_p = tip.css('.tipoprog_content_wrap').xpath('text()').extract()
        ldr.add_value('text', [p.strip() for p in all_p if p.strip()])
        item = ldr.load_item()
        d = {}
        for row in tip.css('.tipoprog_table_small tr'):
            td = row.css('td ::text').extract()
            td.extend(['', ''])
            label = td[0].rstrip(': ').lower()
            d[label] = td[1].strip()
            if label == 'kladionica' and not d[label]:
                d[label] = row.css('td a::attr(title)').extract_first() or ''
        datamap = dict(result='rezultat', tipster='tipster',
                       coeff='koeficijent', min_coeff='min. koef.',
                       stake='ulog', due='zarada', spread='is. margina',
                       betting='kladionica', success=u'uspje\u0161nost',
                       published='objavljeno')
        for dst, src in datamap.items():
            item[dst] = d.get(src, '')
        item['published'] = extract_datetime(item['published'],
                                             fix=True, dayfirst=True)
        return item

    def process_tips_item(self, item):
        pass

    # ############### NEWS ################

    def on_news(self):
        self.clear_cache('all')
        self.logger.info('Crawling news')

    def wd_news_safe(self, response):
        try:
            self.wd_news_unsafe(response)
        except Exception as err:
            self.ercount += 1
            if self.ercount < len(self.news) * 2 + 5:
                self.logger.info('Overriding browser issue %r', err)
                self.send_partial_news()
                randsleep(5)
                # restart from front page
                return WebdriverRequest(
                    self.homepage, callback=self.wd_start,
                    dont_filter=True, meta=dict(dont_cache=True))
            self.logger.info('Too many failures. Baling out.')
        self.logger.info('***** All news ready. Fetching images *****')
        return self.news

    def wd_news_unsafe(self, response):
        self.wd_login(response)
        self.wd_click_menu(response, 'Najave')
        self.loop_on = True
        while self.loop_on:
            self.wd_news_loop(response)

    def wd_news_loop(self, response):
        self.logger.debug('Requesting all news links')
        news_links = response.webdriver.find_elements_by_xpath(
            '//*[contains(@class,"rswcl_najava")]//h3/a')

        if self.numinfo:
            self.numinfo = False
            self.tocrawl = len(news_links)
            self.logger.info('To crawl at most %d news', self.tocrawl)

        for link in news_links:
            url = link.get_attribute('href')
            self.logger.debug('Link %s has url %s', link, url)
            if url in self.skipped or url in self.crawled:
                self.logger.debug('This url has been skipped or crawled')
                continue
            self.logger.debug('Select url %s', url)
            break
        else:
            self.logger.debug('No more urls to try')
            self.loop_on = False
            return

        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', url).group(1))
            self.logger.debug('Exctracted pk %s from url %s', pk, url)
        except Exception:
            self.skipped.add(url)
            self.tocrawl = max(1, self.tocrawl - 1)
            self.logger.warn('Skip archived news %s', url)
            return

        if (not self.single_pk and pk in self.seen) or \
                (self.single_pk and pk != self.single_pk):
            self.skipped.add(url)
            self.tocrawl = max(1, self.tocrawl - 1)
            self.logger.info('News already seen %s', url)
            self.news.append(
                dict(pk=pk, crawled=datetime.utcnow().replace(microsecond=0)))
            return

        self.logger.debug('Clicking on link %s', url)
        link.click()
        self.logger.debug('Waiting for ajax')
        response.wait_for_ajax()
        self.logger.debug('Sleep for ~ %d seconds', self.delay_base)
        randsleep(self.delay_base)
        self.logger.debug('Clear Cache')
        response.clear_cache(safe=True)

        self.logger.debug('Scrape article with pk %s url %s', pk, url)
        self.parse_news(response, url, pk)
        self.crawled.add(url)
        news_count = len(self.crawled)
        self.logger.info('Crawled news #%d of %d %s',
                         news_count, self.tocrawl, url)
        if 0 < self.max_news <= news_count or \
                (self.single_pk and pk == self.single_pk):
            self.logger.debug('Reached configured news limit')
            self.loop_on = False
            return
        if self.delay_base > 10:
            self.send_partial_news(last=1)

        self.logger.debug('Click on the back button')
        response.webdriver.back()
        self.logger.debug('Wait for ajax')
        response.wait_for_ajax()
        self.logger.debug('Clear cache')
        response.clear_cache(safe=True)
        self.logger.debug('Sleep for ~ %d seconds', self.delay_base / 2)
        randsleep(self.delay_base / 2)

    def parse_news(self, response, url, pk):
        ldr = TakeFirstItemLoader(NewsItem(), response)
        ldr.add_value('url', url)
        ldr.add_value('pk', pk)
        ldr.add_value('crawled', datetime.utcnow().replace(microsecond=0))
        ldr.add_css('section', '.lnfl ::text')
        ldr.add_css('subsection', '.lnfl.tename ::text')
        ldr.add_css('updated', '.nls_subt_left ::text')
        ldr.add_css('short_title', '.nlsn_title_text ::text')
        ldr.add_css('title', '.nlsn_content > h2 ::text')
        ldr.add_css('published', '.najva-meta-published > span ::text')
        ldr.add_css('image_urls', '.najava_pic_wrap.floatl > img ::attr(src)')
        ldr.add_css('preamble', '.nlsn_content > h3 ::text')
        ldr.add_css('content', '.nlsn_content > p')
        ldr.add_css('subtable', '.nlsn_table_wrap')
        ldr.add_xpath('subtable2',
                      '//div[@id="nls_najava"]'
                      '/following-sibling::*[name()="ul" or name()="div"]')
        item = ldr.load_item()
        item['subtable'] = u'{}\n<div class="subtable2">\n{}\n</div>'.format(
            item.pop('subtable', ''), item.pop('subtable2', ''))
        if self.with_images:
            item['image_urls'] = [response.urljoin(img_url) for img_url in
                                  item.get('image_urls', [])][:1]
        else:
            item['image_urls'] = []
        self.news.append(item)

    def process_news_item(self, item):
        image_dir = self.settings.get('IMAGES_STORE')
        item['image1_filename'] = ''
        item['image1_base64data'] = ''
        if item.get('images', []):
            image = item['images'][0]
            full_path = os.path.join(image_dir, image['path'])
            file_name = os.path.basename(full_path)
            with open(full_path, 'rb') as fd:
                bin_data = fd.read()
            item['image1_filename'] = file_name
            item['image1_mimetype'] = mimetypes.guess_type(file_name)[0] or ''
            item['image1_base64data'] = bin_data.encode('base64').rstrip()
        del item['images']
        del item['image_urls']

    # ############## SENDING ##############

    def process_store_item(self, item):
        if isinstance(item, NewsItem):
            self.process_news_item(item)
        if isinstance(item, TipsItem):
            self.process_tips_item(item)

    def on_finished(self):
        self.send_to_server(self.news, self.tips)
        self.close_database()

    def send_to_server(self, news, tips, status='finished'):
        datas = dict(news=news, tips=tips)
        for name in sorted(datas.keys()):
            arr = datas[name]
            for no, item in enumerate(arr):
                item = dict(item)
                for date in ('crawled', 'updated', 'published'):
                    if hasattr(item, date):
                        item[date] = str(item[date].replace(microsecond=0))
                    if item.get(date, None):
                        item[date] = str(item[date].replace(microsecond=0))
                arr[no] = dict(item)
        action = ','.join([a for a in self.action_list if a in datas])
        api_request(logger=self.logger, action=action, request='results',
                    starttime=self.starttime,
                    status=status, news=news, tips=tips)

    def send_partial_news(self, last=0):
        news = self.news[:]
        if last > 0:
            last = min(len(news), last)
            news = news[-last:]
        self.logger.debug('Sending partial results')
        try:
            self.send_to_server(news=news, tips=[], status='partial')
        except Exception as err:
            self.logger.info('Sending choked: %s', err)


def api_request(logger, action, request, starttime=None, type=None, **kwargs):
    web_server = WEB_SERVER
    secret = SECRET_KEY
    if not (web_server and secret):
        print 'Requests not active'
        return

    meta = {}
    meta['action'] = action
    meta['type'] = str(type or '')
    meta['pid'] = str(os.getpid())
    meta['stamp'] = str(datetime.utcnow().replace(microsecond=0))
    meta['starttime'] = str(starttime or meta['stamp'])
    meta['host'] = socket.gethostname()
    meta['ipaddr'] = socket.gethostbyname(meta['host'])
    meta['rand'] = str(random.randint(1, 99))

    digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
    meta['digest'] = hashlib.sha1(digest + SECRET_KEY).hexdigest()
    data = kwargs.copy()
    data['meta'] = meta
    status = data.get('status', 'status')

    url = urljoin(web_server, request)
    try:
        res = requests.post(url, json=data).json()
        meta = res.pop('meta', {})
        ref_digest = meta.pop('digest', '')
        digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
        assert hashlib.sha1(digest + SECRET_KEY).hexdigest() == ref_digest
        if logger:
            logger.info('Webserver returned %r for %r (%s)',
                        res, request, status)
        return res
    except Exception as err:
        if logger:
            logger.info('Webserver failed with %r for %r', err, request)
        else:
            print 'Webserver failed with %r for %r' % (err, request)


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
            sleep(POLL_SECONDS)
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
            return self.run_action(action, env)

        res = api_request(logger=self.logger, action='service', type='manual', request='run')
        if res:
            action = res.get('action', None)
            env = res.get('env', {})
            self.last_env = env.copy()
            if action:
                return self.run_action(action, env)

    def run_action(self, action, env):
        from vanko.utils.multiprocessing import Process2
        kwargs = dict(spider_cls=DvoznakSpider, action=action, env=env)
        Process2(target=run_spider, kwargs=kwargs).start()


def getopt(optname, env=None):
    for arg in sys.argv:
        mo = re.match(r'^--%s(?:=(.*))?$' % optname, arg)
        if mo:
            val = mo.group(1) or ''
            if env:
                os.environ[env] = val
            return val
    return None


def main():
    from vanko.scrapy import setup_stderr
    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)

    if getopt('action'):
        return run_spider(DvoznakSpider, argv=True)

    userpass = getopt('userpass')
    if userpass or getopt('service') is not None:
        os.environ['USERPASS'] = userpass or ''
        setup_stderr(__name__, pid_in_name=False)
        return Service().run()


if __name__ == '__main__':
    freeze_support()
    main()
