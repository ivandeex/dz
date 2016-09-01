import re
from datetime import datetime
from .api import send_partial_news
from .spider import DzSpider

from vanko.scrapy import TakeFirstItemLoader, Item, Field, StripField, JoinField, DateTimeField
from vanko.utils import randsleep, as_list
from vanko.scrapy.webdriver import WebdriverRequest, WebdriverResponse


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


class NewsSpider(DzSpider):

    def wd_start(self, response):
        assert isinstance(response, WebdriverResponse)
        result = self.wd_news_safe(response)
        for x in as_list(result):
            yield x

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
                send_partial_news(self.logger, self.news,
                                  self.action_list, self.starttime, last=0)
                randsleep(5)
                # restart from front page
                return WebdriverRequest(
                    self.homepage, callback=self.wd_start,
                    dont_filter=True, meta=dict(dont_cache=True))
            self.logger.info('Too many failures. Baling out.')
        self.logger.info('***** All news ready. *****')
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
            send_partial_news(self.logger, self.news,
                              self.action_list, self.starttime, last=1)

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
        ldr.add_css('preamble', '.nlsn_content > h3 ::text')
        ldr.add_css('content', '.nlsn_content > p')
        ldr.add_css('subtable', '.nlsn_table_wrap')
        ldr.add_xpath('subtable2',
                      '//div[@id="nls_najava"]'
                      '/following-sibling::*[name()="ul" or name()="div"]')
        item = ldr.load_item()
        item['subtable'] = u'{}\n<div class="subtable2">\n{}\n</div>'.format(
            item.pop('subtable', ''), item.pop('subtable2', ''))
        self.news.append(item)
