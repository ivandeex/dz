import re
from urlparse import urljoin
from parsel import Selector
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .utils import logger, extract_datetime, first_text
from .spider import BaseSpider
from .api import api_send_item


DATA_MAP = {
    'result': 'rezultat',
    'tipster': 'tipster',
    'odds': 'koeficijent',
    'min_odds': 'min. koef.',
    'stake': 'ulog',
    'earnings': 'zarada',
    'spread': 'is. margina',
    'bookmaker': 'kladionica',
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

        tip_element_list = self.wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '.tiprog_list_block')
        ))

        for tip_element in tip_element_list:
            self.parse_tip(tip_element)

        self.end()

    def parse_tip(self, tip_elem):
        sel = Selector(tip_elem.get_attribute('innerHTML'))
        relative_url = sel.css('.tpl_right > h3 > a::attr(href)').extract_first()
        link = urljoin(self.webdriver.current_url, relative_url)

        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', link).group(1))
        except Exception:
            logger.info('Skip incomplete tip %s', link)
            return
        item = dict(pk=pk, link=link)

        item['league'] = first_text(sel, '.tpl_right > h3 > span')
        item['parties'] = first_text(sel, '.tpl_right > h3 > a')
        item['title'] = first_text(sel, '.tiprot_left > strong')

        item['updated'] = extract_datetime(first_text(sel, '.tiprot_right'))

        para_list = sel.css('.tipoprog_content_wrap').xpath('text()').extract()
        item['text'] = u' '.join(para.strip() for para in para_list if para.strip())

        data = {}
        for row_elem in tip_elem.find_elements_by_css_selector('.tipoprog_table_small tr'):
            td_text = [td_elem.text for td_elem in row_elem.find_elements_by_tag_name('td')]
            label = td_text[0].strip(': ').lower() if td_text else ''
            value = td_text[1].strip() if len(td_text) > 1 else ''

            if not value and label == 'kladionica':
                a_elems = row_elem.find_elements_by_css_selector('td a[title]')
                value = a_elems[0].get_attribute('title') if a_elems else ''

            if not value and label == u'uspje\u0161nost':
                span_elems = row_elem.find_elements_by_xpath('td[2]/span')
                if span_elems:
                    bg_image = span_elems[0].value_of_css_property('background-image') or ''
                    match = re.search(r'^url\(.*/([^.]+)\.(png|gif|jpg)\)$', bg_image.strip())
                    if match:
                        value = match.group(1).strip().lower()
                        value = SUCCESS_BG_IMAGE_MAP.get(value, '')

            data[label] = value

        for dst, src in DATA_MAP.items():
            item[dst] = data.get(src, '')

        item['published'] = extract_datetime(item['published'])

        # if publish date is not found, default to update date
        item['published'] = item['published'] or item['updated']

        self.crawled_ids.add(pk)
        api_send_item(self.target, self.start_utc, self.debug, item)
