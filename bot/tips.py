import re
from urlparse import urljoin
from .utils import logger, extract_datetime, first_text
from .spider import BaseSpider
from .api import api_send_item


DATA_MAP = {
    'result': 'rezultat',
    'tipster': 'tipster',
    'rate': 'koeficijent',
    'minrate': 'min. koef.',
    'stake': 'ulog',
    'earnings': 'zarada',
    'spread': 'is. margina',
    'betting': 'kladionica',
    'success': u'uspje\u0161nost',
    'published': 'objavljeno',
}


class TipsSpider(BaseSpider):
    target = 'tips'

    def run(self):
        self.login()
        self.click_menu('Prognoze')
        for sel in self.wait_for_css('.tiprog_list_block'):
            item = self.parse_tip(sel)
            if item:
                self.crawled_ids.add(item['id'])
                api_send_item(self.target, self.start_time, self.debug, item)

    def parse_tip(self, sel):
        item = {}
        rel_url = sel.css('.tpl_right > h3 > a::attr(href)').extract_first()
        link = urljoin(self.webdriver.current_url, rel_url)

        try:
            id = int(re.search(r'id_dogadjaj=(\d+)', link).group(1))
        except Exception:
            logger.info('Skip tip %s', link)
            return
        item['id'] = id
        item['link'] = link

        item['league'] = first_text(sel, '.tpl_right > h3 > span')
        item['parties'] = first_text(sel, '.tpl_right > h3 > a')
        item['title'] = first_text(sel, '.tiprot_left > strong')

        item['updated'] = extract_datetime(first_text(sel, '.tiprot_right'))

        all_p = sel.css('.tipoprog_content_wrap').xpath('text()').extract()
        item['text'] = u' '.join(p.strip() for p in all_p if p.strip())

        d = {}
        for row in sel.css('.tipoprog_table_small tr'):
            td = row.css('td ::text').extract()
            td.extend(['', ''])
            label = td[0].rstrip(': ').lower()
            d[label] = td[1].strip()
            if label == 'kladionica' and not d[label]:
                d[label] = row.css('td a::attr(title)').extract_first() or ''

        for dst, src in DATA_MAP.items():
            item[dst] = d.get(src, '')

        item['published'] = extract_datetime(item['published'])

        # if publish date not found, default to update date
        item['published'] = item['published'] or item['updated']
        return item
