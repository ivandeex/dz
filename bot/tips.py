import re
from datetime import datetime
from vanko.scrapy import TakeFirstItemLoader, Item, Field, StripField, JoinField, DateTimeField
from vanko.utils import extract_datetime
from vanko.scrapy.webdriver import WebdriverResponse
from .spider import DzSpider


class TipsItem(Item):
    pk = Field()
    place = StripField()
    title = StripField()
    tip = StripField()
    published = DateTimeField(fix=True, dayfirst=True)
    updated = DateTimeField(fix=True, dayfirst=True)
    text = JoinField(sep=' ')
    result = Field()
    tipster = Field()
    coeff = Field()
    min_coeff = Field()
    stake = Field()
    due = Field()
    spread = Field()
    betting = Field()
    success = Field()
    details_url = Field()
    crawled = Field()


class TipsSpider(DzSpider):

    def wd_start(self, response):
        assert isinstance(response, WebdriverResponse)
        self.wd_login(response)
        self.wd_click_menu(response, 'Prognoze')
        self.tips_list(response)

    def on_tips(self):
        self.clear_cache('all')
        self.logger.info('Crawling tips')

    def tips_list(self, response):
        tiplist = response.wait_css('.tiprog_list_block')
        for tip in tiplist:
            item = self.parse_tip(tip, response)
            if item:
                self.tips.append(item)

    def parse_tip(self, tip, response):
        ldr = TakeFirstItemLoader(TipsItem(), tip)
        details_url = response.urljoin(
            tip.css('.tpl_right > h3 > a ::attr(href)').extract_first())
        try:
            pk = int(re.search(r'id_dogadjaj=(\d+)', details_url).group(1))
        except Exception:
            self.logger.info('Skipping tip %s', details_url)
            return
        ldr.add_value('pk', pk)
        ldr.add_value('details_url', details_url)
        ldr.add_value('crawled', datetime.utcnow().replace(microsecond=0))

        ldr.add_css('place', '.tpl_right > h3 > span ::text')
        ldr.add_css('title', '.tpl_right > h3 > a ::text')
        ldr.add_css('tip', '.tiprot_left > strong ::text')
        ldr.add_css('updated', '.tiprot_right ::text')
        all_p = tip.css('.tipoprog_content_wrap').xpath('text()').extract()
        ldr.add_value('text', [p.strip() for p in all_p if p.strip()])
        item = ldr.load_item()
        d = {}
        for row in tip.css('.tipoprog_table_small tr'):
            td = row.css('td ::text').extract()
            td.extend(['', ''])
            label = td[0].rstrip(': ').lower()
            d[label] = td[1].strip()
            if label == 'kladionica' and not d[label]:
                d[label] = row.css('td a::attr(title)').extract_first() or ''
        datamap = dict(result='rezultat', tipster='tipster',
                       coeff='koeficijent', min_coeff='min. koef.',
                       stake='ulog', due='zarada', spread='is. margina',
                       betting='kladionica', success=u'uspje\u0161nost',
                       published='objavljeno')
        for dst, src in datamap.items():
            item[dst] = d.get(src, '')
        item['published'] = extract_datetime(item['published'], fix=True, dayfirst=True)
        return item
