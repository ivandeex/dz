import re
from .api import api_send_item
from .spider import BaseSpider
from .utils import logger, extract_datetime, first_text, randsleep, split_ranges


class NewsSpider(BaseSpider):
    target = 'news'

    def __init__(self, env):
        self.seen_news = split_ranges(env.get('SEEN_NEWS', '').strip())
        self.skipped_urls = set()
        self.crawled_urls = set()
        self.num_info = True
        self.to_crawl = 0
        self.err_count = 0
        self.looping = True
        super(NewsSpider, self).__init__(env)

    def run(self):
        self.login()
        self.click_menu('Najave')
        while self.looping:
            try:
                self.next_news()
            except Exception as err:
                logger.error('Browser issue %r', err)
                if self.debug:
                    raise
                self.err_count += 1
                if self.err_count > len(self.news) * 2 + 5:
                    break
                randsleep(5)

    def next_news(self):
        logger.debug('Requesting all news links')
        xpath = '//*[contains(@class,"rswcl_najava")]//h3/a'
        news_links = self.webdriver.find_elements_by_xpath(xpath)

        if self.num_info:
            self.num_info = False
            self.to_crawl = len(news_links)
            logger.info('To crawl at most %d news', self.to_crawl)

        for link in news_links:
            url = link.get_attribute('href')
            if url in self.skipped_urls:
                logger.debug('Skipped url %s', url)
                continue
            if url in self.crawled_urls:
                logger.debug('Already crawled url %s', url)
                continue
            logger.debug('Select url %s', url)
            break
        else:
            logger.debug('No more urls to try')
            self.looping = False
            return

        try:
            id = int(re.search(r'id_dogadjaj=(\d+)', url).group(1))
            logger.debug('Exctracted id %s from url %s', id, url)
        except Exception:
            self.skipped_urls.add(url)
            self.to_crawl = max(1, self.to_crawl - 1)
            logger.warn('Skip invalid url %s', url)
            return

        if id in self.seen_news:
            self.skipped_urls.add(url)
            self.to_crawl = max(1, self.to_crawl - 1)
            logger.info('News already seen %s', url)
            return

        logger.debug('Clicking on link %s', url)
        link.click()
        logger.debug('Waiting for ajax')
        self.wait_for_ajax()
        logger.debug('Sleep ~ %d sec before page', self.page_delay)
        randsleep(self.page_delay)

        logger.debug('Scrape article with id %s url %s', id, url)
        item = self.parse_news(url, id)
        logger.info('Crawled news #%d of %d, %s',
                    len(self.crawled_ids) + 1, self.to_crawl, url)
        self.crawled_urls.add(url)
        self.crawled_ids.add(id)
        api_send_item(self.target, self.start_utc, self.debug, item)

        logger.debug('Click on the back button')
        self.webdriver.back()

        logger.debug('Wait for ajax')
        self.wait_for_ajax()

        logger.debug('Sleep ~ %d sec after page', self.page_delay)
        randsleep(self.page_delay)

    def parse_news(self, url, id):
        sel = self.page_sel()
        item = {}

        item['link'] = url
        item['id'] = id

        item['sport'] = first_text(sel, '.lnfl')
        item['league'] = first_text(sel, '.lnfl.tename')
        item['parties'] = first_text(sel, '.nlsn_title_text')
        item['title'] = first_text(sel, '.nlsn_content > h2')

        item['updated'] = extract_datetime(first_text(sel, '.nls_subt_left'))
        item['published'] = extract_datetime(first_text(sel, '.najva-meta-published > span'))

        item['preamble'] = first_text(sel, '.nlsn_content > h3')
        item['content'] = '\n'.join(x.strip() for x in sel.css('.nlsn_content > p').extract())

        subtable1 = '\n'.join(x.strip() for x in sel.css('.nlsn_table_wrap').extract())
        subtable2_xp = '//div[@id="nls_najava"]/following-sibling::*[name()="ul" or name()="div"]'
        subtable2 = '\n'.join(x.strip() for x in sel.xpath(subtable2_xp).extract())
        item['subtable'] = u'%s\n<div class="subtable2">\n%s\n</div>' % (subtable1, subtable2)

        return item
