import re
from .api import api_send_item
from .spider import BaseSpider
from .utils import logger, extract_datetime, first_text, randsleep, split_ranges


class NewsSpider(BaseSpider):
    target = 'news'

    def __init__(self, env):
        self.seen_news = split_ranges(env.get('SEEN_NEWS', '').strip())
        self.done_urls = set()
        self.todo = None
        self.err_count = 0
        self.looping = True
        super(NewsSpider, self).__init__(env)

    def run(self):
        self.login()
        self.click_menu('Najave')
        while self.looping:
            try:
                self.crawl_next_news()
            except Exception as err:
                logger.error('Browser issue %r', err)
                if self.debug:
                    raise
                self.err_count += 1
                if self.err_count > len(self.news) * 2 + 5:
                    break
                randsleep(5)

    def crawl_next_news(self):
        news_links = self.webdriver.find_elements_by_css_selector('.rswcl_najava h3 > a')
        if self.todo is None:
            self.todo = len(news_links)
            logger.info('Will crawl at most %d news', self.todo)

        id = None
        for link in news_links:
            url = link.get_attribute('href')
            if url in self.done_urls:
                continue
            self.done_urls.add(url)

            try:
                id = int(re.search(r'id_dogadjaj=(\d+)', url).group(1))
            except Exception:
                self.todo = max(self.todo - 1, 1)
                logger.warn('Invalid news url %s', url)
                continue

            if id not in self.seen_news:
                break
            # skip this url but mark as fresh
            self.crawled_ids.add(id)
            self.todo = max(1, self.todo - 1)
            logger.info('News already crawled %s', url)

        if id is None:
            self.looping = False
            return

        logger.debug('Crawl news %d from %s', id, url)
        link.click()
        self.wait_for_ajax()
        randsleep(5)

        item = self.parse_news(url, id)
        logger.info('Crawled news #%d of %d, %s', len(self.crawled_ids) + 1, self.todo, url)
        self.crawled_ids.add(id)
        api_send_item(self.target, self.start_utc, self.debug, item)

        logger.debug('Go back and sleep ~ %d sec', self.page_delay)
        self.webdriver.back()
        self.wait_for_ajax()
        randsleep(self.page_delay)

    def parse_news(self, url, id):
        sel = self.page_sel()
        item = dict(link=url, id=id)

        item['sport'] = first_text(sel, '.lnfl')
        item['league'] = first_text(sel, '.lnfl.tename')
        item['parties'] = first_text(sel, '.nlsn_title_text')
        item['title'] = first_text(sel, '.nlsn_content > h2')

        item['updated'] = extract_datetime(first_text(sel, '.nls_subt_left'))
        item['published'] = extract_datetime(first_text(sel, '.najva-meta-published > span'))

        item['preamble'] = first_text(sel, '.nlsn_content > h3')
        item['content'] = '\n'.join(p.strip() for p in sel.css('.nlsn_content > p').extract())

        table1 = '\n'.join(html.strip() for html in sel.css('.nlsn_table_wrap').extract())
        xpath = '//div[@id="nls_najava"]/following-sibling::*[name()="ul" or name()="div"]'
        table2 = '\n'.join(html.strip() for html in sel.xpath(xpath).extract())
        item['subtable'] = u'%s\n<div class="subtable2">\n%s\n</div>' % (table1, table2)

        return item
