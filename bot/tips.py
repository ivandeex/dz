import re
from datetime import datetime
from urlparse import urljoin
from .utils import logger, extract_datetime, first_text
from .spider import BaseSpider


DATA_MAP = {
    'result': 'rezultat',
    'tipster': 'tipster',
    'coeff': 'koeficijent',
    'min_coeff': 'min. koef.',
    'stake': 'ulog',
    'due': 'zarada',
    'spread': 'is. margina',
    'betting': 'kladionica',
    'success': u'uspje\u0161nost',
    'published': 'objavljeno',
}


class TipsSpider(BaseSpider):
    action = 'tips'

    def run(self):
        self.login()
        self.click_menu('Prognoze')
        for sel in self.wait_for_css('.tiprog_list_block'):
            self.parse_tip(sel)

    def parse_tip(self, sel):
        item = {}
        rel_url = sel.css('.tpl_right > h3 > a::attr(href)').extract_first()
        details_url = urljoin(self.webdriver.current_url, rel_url)

        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', details_url).group(1))
        except Exception:
            logger.info('Skipping tip %s', details_url)
            return
        item['pk'] = pk

        item['details_url'] = details_url
        item['crawled'] = datetime.utcnow().replace(microsecond=0)

        item['place'] = first_text(sel, '.tpl_right > h3 > span')
        item['title'] = first_text(sel, '.tpl_right > h3 > a')
        item['tip'] = first_text(sel, '.tiprot_left > strong')

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
        self.tips.append(item)
