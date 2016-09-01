import re
from datetime import datetime
from parsel import Selector
from vanko.utils import randsleep, as_list
from vanko.scrapy.webdriver import WebdriverRequest
from .api import send_partial_news
from .spider import DzSpider
from .utils import extract_datetime, first_text


class NewsSpider(DzSpider):

    def wd_start(self, response):
        for x in as_list(self.wd_news_safe(response)):
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
        sel = Selector(text=response.get_body())
        item = {}

        item['url'] = url
        item['pk'] = pk
        item['crawled'] = datetime.utcnow().replace(microsecond=0)

        item['section'] = first_text(sel, '.lnfl')
        item['subsection'] = first_text(sel, '.lnfl.tename')
        item['short_title'] = first_text(sel, '.nlsn_title_text')
        item['title'] = first_text(sel, '.nlsn_content > h2')

        item['updated'] = first_text(sel, '.nls_subt_left')
        item['updated'] = extract_datetime(item['updated'], fix=True, dayfirst=True)
        item['published'] = first_text(sel, '.najva-meta-published > span')
        item['published'] = extract_datetime(item['published'], fix=True, dayfirst=True)

        item['preamble'] = first_text(sel, '.nlsn_content > h3')
        item['content'] = '\n'.join(x.strip() for x in sel.css('.nlsn_content > p').extract())

        subtable1 = '\n'.join(x.strip() for x in sel.css('.nlsn_table_wrap').extract())
        subtable2_xp = '//div[@id="nls_najava"]/following-sibling::*[name()="ul" or name()="div"]'
        subtable2 = '\n'.join(x.strip() for x in sel.xpath(subtable2_xp).extract())
        item['subtable'] = u'%s\n<div class="subtable2">\n%s\n</div>' % (subtable1, subtable2)

        self.news.append(item)
