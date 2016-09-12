import re
from .api import api_send_item
from .spider import BaseSpider
from .utils import logger, extract_datetime, first_text, randsleep, split_ranges


class NewsSpider(BaseSpider):
    target = 'news'

    def __init__(self, env):
        self.seen_news = split_ranges(env.get('SEEN_NEWS', '').strip())
        self.single_id = int(env.get('NEWS_ID', 0))
        self.done_urls = set()
        self.todo = None
        self.err_count = 0
        super(NewsSpider, self).__init__(env)

    def run(self):
        self.login()

        if self.single_id:
            url_fmt = 'http://www.dvoznak.com/?show=dogadjaj&id_dogadjaj=%d&id_vrsta_dogadjaja=1'
            url = url_fmt % self.single_id
            self.webdriver.get(url)
            self.parse_news(url, self.single_id)
            return

        self.click_menu('Najave')

        while True:
            try:
                url, id = self.get_next_news()
                if not url:
                    break
                self.parse_news(url, id)

                logger.debug('Go back and sleep ~ %d sec', self.page_delay)
                self.webdriver.back()
                self.wait_for_ajax()
                randsleep(self.page_delay)

            except Exception as err:
                logger.error('Webdriver error: %r', err)
                if self.debug:
                    raise
                self.err_count += 1
                if self.err_count > len(self.news) * 2 + 5:
                    break
                randsleep(5)

        self.end()

    def get_next_news(self):
        news_links = self.webdriver.find_elements_by_css_selector('.rswcl_najava h3 > a')
        if self.todo is None:
            self.todo = len(news_links)
            logger.info('Will crawl at most %d news', self.todo)

        for link in news_links:
            url = link.get_attribute('href')
            if url in self.done_urls:
                continue
            self.done_urls.add(url)

            try:
                id = int(re.search(r'id_dogadjaj=(\d+)', url).group(1))
            except Exception:
                self.todo -= 1
                logger.warn('Invalid news url %s', url)
                continue

            if id not in self.seen_news:
                link.click()
                return url, id

            # skip this url but mark as fresh
            self.crawled_ids.add(id)
            self.todo -= 1
            logger.info('News already crawled %s', url)

        return None, None

    def parse_news(self, url, id):
        logger.debug('Crawling news %d from %s', id, url)
        self.wait_for_ajax()
        randsleep(5)

        sel = self.page_sel()
        item = dict(link=url, id=id)

        item['sport'] = first_text(sel, '.lnfl')
        item['league'] = first_text(sel, '.lnfl.tename').partition(',')[0]
        item['parties'] = first_text(sel, '.nlsn_title_text')
        item['title'] = first_text(sel, '.nlsn_content > h2')

        item['updated'] = extract_datetime(first_text(sel, '.nls_subt_left'))
        item['published'] = extract_datetime(first_text(sel, '.najva-meta-published > span'))

        item['newstext.preamble'] = first_text(sel, '.nlsn_content > h3')

        text = []
        content_node = sel.css('.nlsn_content')
        xpath = './node()[name()="p" or name()="b" or self::text()]'
        for para in content_node.xpath(xpath).extract():
            para = para.strip()
            if para and para != u'<p></p>':
                if not para.startswith(u'<p>'):
                    para = u'<p>' + para + u'</p>'
                text.append(para)
        item['newstext.content'] = u'\n'.join(text)

        table1 = '\n'.join(html.strip() for html in sel.css('.nlsn_table_wrap').extract())
        xpath = '//div[@id="nls_najava"]/following-sibling::*[name()="ul" or name()="div"]'
        table2 = '\n'.join(html.strip() for html in sel.xpath(xpath).extract())
        item['newstext.datatable'] = u'%s\n<div class="subtable2">\n%s\n</div>' % (table1, table2)

        self.crawled_ids.add(id)
        api_send_item(self.target, self.start_utc, self.debug, item)
        logger.info('Crawled news #%d of %d from %s',
                    len(self.crawled_ids), max(self.todo or 0, 1), url)
