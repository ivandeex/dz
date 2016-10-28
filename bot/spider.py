import os
import tempfile
from selenium.webdriver import PhantomJS, DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import logger, randsleep
from .api import api_send_complete, naive2api

DEFAULT_PAGE_DELAY = 50


class BaseSpider(object):
    user_agent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    home_url = ''.join(['http://', 'www.', 'dv', 'ozn', 'ak', '.com/'])
    timeout = 30
    target = None

    def __init__(self, env):
        self.start_utc = env.get('START_UTC', naive2api())
        self.page_delay = int(env.get('PAGE_DELAY', DEFAULT_PAGE_DELAY))
        self.load_images = bool(int(env.get('LOAD_IMAGES', True)))
        self.debug = bool(int(env.get('DEBUG', False)))
        self.username, _, self.password = env.get('USERPASS', '').partition(':')

        self.crawled_ids = set()

        caps = DesiredCapabilities.PHANTOMJS.copy()
        caps['phantomjs.page.settings.userAgent'] = self.user_agent

        self.webdriver = PhantomJS(
            executable_path=env.get('PHANTOMJS_BINARY', 'phantomjs'),
            desired_capabilities=caps,
            service_args=([] if self.load_images else ['--load-images=no']),
            service_log_path=os.path.join(tempfile.gettempdir(), 'phantomjs.log')
        )

        self.webdriver.get(self.home_url)

    def end(self):
        logger.info('Crawling complete')
        api_send_complete(self.target, self.start_utc, self.debug, self.crawled_ids)

    def close(self):
        self.webdriver.quit()
        self.webdriver = None

    def login(self):
        self.wait_for_ajax()
        wait = WebDriverWait(self.webdriver, self.timeout)

        if not (self.username and self.password):
            logger.info('Working without login')
            return

        # opening login drawer
        el = wait.until(EC.element_to_be_clickable((By.ID, 'login_btn')))
        el.click()

        # fill login form
        el = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'form[name="prijava"] input[type="text"]')))
        el.send_keys(self.username)

        el = self.webdriver.find_element_by_css_selector(
            'form[name="prijava"] input[type="password"]')
        el.send_keys(self.password)

        # click login button
        el = wait.until(EC.element_to_be_clickable((By.NAME, 'Prijava')))
        el.click()

        wait.until(EC.visibility_of_element_located((By.LINK_TEXT, 'Moj profil')))
        logger.info('Logged in as %s', self.username)

    def click_menu(self, menu):
        logger.debug('Click on menu "%s"', menu)
        wait = WebDriverWait(self.webdriver, self.timeout)
        css = '#mainmenu a[href*="%s"]' % menu.lower()
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        el.click()
        self.wait_for_ajax()

    def wait_for_ajax(self):
        def ajax_request_count(driver):
            return sum(filter(bool, driver.execute_script(
                'return [window.jQuery && window.jQuery.active, '
                'window.Ajax && window.Ajax.activeRequestCount, '
                'window.dojo && window.io.XMLHTTPTransport.inFlight.length];')))
        WebDriverWait(self.webdriver, self.timeout).until_not(ajax_request_count)
        randsleep(2)
