import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from .api import send_results

from vanko.scrapy import CustomSettings, CustomSpider, setup_spider
from vanko.utils import decode_userpass, randsleep
from vanko.scrapy.webdriver import WebdriverRequest


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
    STARTTIME='',
)


def split_ranges(range_str):
    res = set()
    if range_str:
        for token in range_str.split(','):
            if '-' in token:
                beg, end = token.split('-')
                for val in range(int(beg), int(end) + 1):
                    res.add(val)
            else:
                res.add(int(token))
    return res


class DzSpider(CustomSpider):

    name = BOT_NAME
    allowed_domains = ['dvoznak.com']
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36'
    login_pending = True
    homepage = 'http://www.dvoznak.com/'

    def __init__(self, *args, **kwargs):
        s = self.settings_init
        self.username, self.password = decode_userpass(s.get('USERPASS'))
        self.starttime = s.get('STARTTIME') or str(datetime.utcnow().replace(microsecond=0))
        self.delay_base = s.getint('DOWNLOAD_DELAY', 40)
        self.max_news = s.getint('MAX_NEWS', 0)
        self.single_pk = s.getint('SINGLE_PK', 0)

        self.seen = split_ranges(s.get('NEWS_TO_SKIP', '').strip())

        self.news = []
        self.tips = []
        self.crawled = set()
        self.skipped = set()
        self.numinfo = True
        self.tocrawl = 0
        self.ercount = 0

    def on_finished(self):
        send_results(self.logger, self.news, self.tips,
                     self.action_list, self.starttime, 'finished')
        self.close_database()

    def start_requests(self):
        yield WebdriverRequest(
            self.homepage, callback=self.wd_start,
            dont_filter=True, meta=dict(dont_cache=True))

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
