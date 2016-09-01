import re
from datetime import datetime
from vanko.utils import randsleep
from .api import send_partial_news
from .spider import BaseSpider
from .main import logger
from .utils import extract_datetime, first_text


class NewsSpider(BaseSpider):
    action = 'news'

    def run(self):
        try:
            self.login()
            self.click_menu('Najave')
            self.loop_on = True
            while self.loop_on:
                self.news_loop()
        except Exception as err:
            self.ercount += 1
            if self.ercount < len(self.news) * 2 + 5:
                logger.info('Overriding browser issue %r', err)
                send_partial_news(self.news, self.starttime, last=0)
                randsleep(5)
            logger.info('Too many failures. Baling out.')

    def news_loop(self):
        logger.debug('Requesting all news links')
        xpath = '//*[contains(@class,"rswcl_najava")]//h3/a'
        news_links = self.webdriver.find_elements_by_xpath(xpath)

        if self.numinfo:
            self.numinfo = False
            self.tocrawl = len(news_links)
            logger.info('To crawl at most %d news', self.tocrawl)

        for link in news_links:
            url = link.get_attribute('href')
            logger.debug('Link %s has url %s', link, url)
            if url in self.skipped or url in self.crawled:
                logger.debug('This url has been skipped or crawled')
                continue
            logger.debug('Select url %s', url)
            break
        else:
            logger.debug('No more urls to try')
            self.loop_on = False
            return

        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', url).group(1))
            logger.debug('Exctracted pk %s from url %s', pk, url)
        except Exception:
            self.skipped.add(url)
            self.tocrawl = max(1, self.tocrawl - 1)
            logger.warn('Skip archived news %s', url)
            return

        if (not self.single_pk and pk in self.seen) or (self.single_pk and pk != self.single_pk):
            self.skipped.add(url)
            self.tocrawl = max(1, self.tocrawl - 1)
            logger.info('News already seen %s', url)
            self.news.append(dict(pk=pk, crawled=datetime.utcnow().replace(microsecond=0)))
            return

        logger.debug('Clicking on link %s', url)
        link.click()
        logger.debug('Waiting for ajax')
        self.wait_for_ajax()
        logger.debug('Sleep for ~ %d seconds', self.delay_base)
        randsleep(self.delay_base)

        logger.debug('Scrape article with pk %s url %s', pk, url)
        self.parse_news(url, pk)
        self.crawled.add(url)
        news_count = len(self.crawled)
        logger.info('Crawled news #%d of %d %s', news_count, self.tocrawl, url)
        if 0 < self.max_news <= news_count or (self.single_pk and pk == self.single_pk):
            logger.debug('Reached configured news limit')
            self.loop_on = False
            return
        send_partial_news(self.news, self.starttime, last=1)

        logger.debug('Click on the back button')
        self.webdriver.back()

        logger.debug('Wait for ajax')
        self.wait_for_ajax()

        logger.debug('Sleep ~%ds', self.delay)
        randsleep(self.delay)

    def parse_news(self, url, pk):
        sel = self.page_sel()
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
