import os
import tempfile
from time import time
from datetime import datetime
from parsel import Selector
from selenium.webdriver import PhantomJS, DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from .utils import logger, randsleep, poll_sleep
from .api import send_results


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


class BaseSpider(object):
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36'
    login_pending = True
    home_url = 'http://www.dvoznak.com/'
    timeout = 60
    action = None

    def __init__(self, env={}):
        self.starttime = env.get('STARTTIME', str(datetime.utcnow().replace(microsecond=0)))
        self.delay = int(env.get('PAGE_DELAY', 20))
        self.seen = split_ranges(env.get('NEWS_TO_SKIP', '').strip())
        self.single_pk = int(env.get('SINGLE_PK', 0))

        self.news = []
        self.tips = []
        self.crawled = set()
        self.skipped = set()
        self.numinfo = True
        self.tocrawl = 0
        self.ercount = 0

        caps = DesiredCapabilities.PHANTOMJS.copy()
        caps['phantomjs.page.settings.userAgent'] = self.user_agent

        self.webdriver = PhantomJS(
            executable_path=env.get('PHANTOMJS_BINARY', 'phantomjs'),
            desired_capabilities=caps,
            service_args=['--load-images=no'],
            service_log_path=os.path.join(tempfile.gettempdir(), 'phantomjs.log')
        )

        self.webdriver.get(self.home_url)

    def close(self):
        try:
            send_results(self.news, self.tips, self.action, self.starttime, 'finished')
        finally:
            self.webdriver.quit()
            self.webdriver = None

    def page_sel(self):
        return Selector(self.webdriver.page_source)

    def login(self):
        self.wait_for_ajax()
        randsleep(2)

        username, _sep, password = os.environ.get('USERPASS', '').partition(':')
        if not (username and password):
            logger.info('Working without login (browser)')
            return

        page_sel = self.page_sel()
        form = page_sel.css('form[name="prijava"]')
        id_user = form.css('input[type="text"]::attr(id)').extract_first()
        id_pass = form.css('input[type="password"]::attr(id)').extract_first()

        logger.debug('Opening login drawer')
        self.click('login_btn', by=By.ID)
        self.wait_for_ajax()
        randsleep(2)

        logger.debug('Filling the form')
        self.send_keys(id_user, self.username)
        self.send_keys(id_pass, self.password)
        randsleep(2)

        logger.debug('Click the login button')
        self.click('Prijava', by=By.NAME)
        randsleep(4)

        logger.info('Logged in as %s (browser)', username)

    def click_menu(self, menu):
        logger.debug('Searching for %s menu', menu)
        xpath = '//ul[@id="mainmenu"]/li/a[contains(.,"%s")]' % menu
        el = self.webdriver.find_element_by_xpath(xpath)
        logger.debug('Clicking on %s menu', menu)
        el.click()

        logger.debug('Waiting for menu ajax to finish')
        self.wait_for_ajax()
        logger.debug('Safety delay after click')
        randsleep(4)

    def wait_for_css(self, css):
        end_time = time() + self.timeout
        while time() < end_time:
            result = self.page_sel().css(css)
            if result:
                return result
            poll_sleep(end_time)

    def wait_for_ajax(self):
        end_time = time() + self.timeout
        while time() < end_time:
            ajax_counts = self.webdriver.execute_script(
                'return [window.jQuery && window.jQuery.active, '
                'window.Ajax && window.Ajax.activeRequestCount, '
                'window.dojo && window.io.XMLHTTPTransport.inFlight.length];')
            if not any(ajax_counts):
                return True
            poll_sleep(end_time)

    def send_keys(self, id, keys):
        el = self.webdriver.find_element_by_id(id)
        el.clear()
        el.send_keys(keys)

    def click(self, id, by):
        cond = expected_conditions.element_to_be_clickable((by, id))
        el = WebDriverWait(self.webdriver, self.timeout).until(cond)
        logger.debug('now click %s', id)
        el.click()
