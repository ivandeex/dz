import re
from datetime import datetime
from parsel import Selector
from .utils import extract_datetime, first_text
from .spider import DzSpider


DATAMAP = dict(
    result='rezultat',
    tipster='tipster',
    coeff='koeficijent',
    min_coeff='min. koef.',
    stake='ulog',
    due='zarada',
    spread='is. margina',
    betting='kladionica',
    success=u'uspje\u0161nost',
    published='objavljeno',
)


class TipsSpider(DzSpider):

    def wd_start(self, response):
        self.wd_login(response)
        self.wd_click_menu(response, 'Prognoze')
        self.tips_list(response)

    def on_tips(self):
        self.clear_cache('all')
        self.logger.info('Crawling tips')

    def tips_list(self, response):
        response.wait_css('.tiprog_list_block')
        for sel in Selector(text=response.get_body()).css('.tiprog_list_block'):
            self.parse_tip(sel, response)

    def parse_tip(self, sel, response):
        item = {}
        rel_url = sel.css('.tpl_right > h3 > a::attr(href)').extract_first()
        details_url = response.urljoin(rel_url)

        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', details_url).group(1))
        except Exception:
            self.logger.info('Skipping tip %s', details_url)
            return
        item['pk'] = pk

        item['details_url'] = details_url
        item['crawled'] = datetime.utcnow().replace(microsecond=0)

        item['place'] = first_text(sel, '.tpl_right > h3 > span')
        item['title'] = first_text(sel, '.tpl_right > h3 > a')
        item['tip'] = first_text(sel, '.tiprot_left > strong')

        item['updated'] = first_text(sel, '.tiprot_right')
        item['updated'] = extract_datetime(item['updated'], fix=True, dayfirst=True)

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

        for dst, src in DATAMAP.items():
            item[dst] = d.get(src, '')

        item['published'] = extract_datetime(item['published'], fix=True, dayfirst=True)
        self.tips.append(item)
