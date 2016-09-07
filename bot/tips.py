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

SUCCESS_BG_IMAGE_MAP = {
    'question': 'unknown',
    'check': 'hit',
    'cross': 'miss',
}


class TipsSpider(BaseSpider):
    target = 'tips'

    def run(self):
        self.login()
        self.click_menu('Prognoze')

        tip_css = '.tiprog_list_block'
        tip_selectors = self.wait_for_css(tip_css)
        tip_elements = self.webdriver.find_elements_by_css_selector(tip_css)

        for tip_sel, tip_elem in zip(tip_selectors, tip_elements):
            item = self.parse_tip(tip_sel, tip_elem)
            if item:
                self.crawled_ids.add(item['id'])
                api_send_item(self.target, self.start_time, self.debug, item)

    def parse_tip(self, sel, elem):
        item = {}
        rel_url = sel.css('.tpl_right > h3 > a::attr(href)').extract_first()
        link = urljoin(self.webdriver.current_url, rel_url)

        try:
            id = int(re.search(r'id_dogadjaj=(\d+)', link).group(1))
        except Exception:
            logger.info('Skip incomplete tip %s', link)
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
        table_css = '.tipoprog_table_small tr'
        row_selectors = sel.css(table_css)
        row_elements = elem.find_elements_by_css_selector(table_css)

        for row_sel, row_elem in zip(row_selectors, row_elements):
            td = row_sel.css('td ::text').extract()
            td.extend(['', ''])
            label = td[0].rstrip(': ').lower()
            value = td[1].strip()

            if not value and label == 'kladionica':
                value = row_sel.css('td a::attr(title)').extract_first() or ''

            if not value and label == u'uspje\u0161nost':
                td2_span = row_elem.find_elements_by_xpath('td[2]/span')
                if td2_span:
                    bg_image = td2_span[0].value_of_css_property('background-image') or ''
                    match = re.search(r'^url\(.*/([^.]+)\.(png|gif|jpg)\)$', bg_image.strip())
                    if match:
                        value = match.group(1).strip().lower()
                        value = SUCCESS_BG_IMAGE_MAP.get(value, '')

            d[label] = value

        for dst, src in DATA_MAP.items():
            item[dst] = d.get(src, '')

        item['published'] = extract_datetime(item['published'])

        # if publish date not found, default to update date
        item['published'] = item['published'] or item['updated']
        return item
