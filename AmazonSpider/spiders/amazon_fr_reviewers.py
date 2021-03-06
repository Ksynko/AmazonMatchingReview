import string

from scrapy.http import Request
from scrapy.log import ERROR, WARNING, INFO, DEBUG

from AmazonSpider.items import ReviewItem
from __init__ import cond_set, cond_set_value, AmazonBaseClass

class AmazonSpider(AmazonBaseClass):
    name = 'amazon_fr_reviewers'
    allowed_domains = ["www.amazon.fr"]
    start_urls = ['http://www.amazon.fr/review/top-reviewers']

    MAX_RETRIES = 3

    user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) Gecko'
                  '/20100101 Firefox/35.0')

    COUNTRY = 'fr'

    def parse_links(self, response):
        links = response.xpath('//tr[contains(@id, "reviewer")]')
        for link in links:
            url = link.xpath('./td[@class="img"]/a[1]/@href').extract()
            item = ReviewItem()

            rank = link.xpath(
                './td[@class="crNum"]/text()').re('#\s?(\d+.?\d{0,})')

            if rank:
                rank = int(rank[0].replace('.', ''))
                item['rank'] = rank
                meta = {'item': item}
                yield Request('http://www.amazon.fr'+url[0],
                              meta=meta,
                              callback=self.parse_email)

        next_page = response.xpath(
            '//a[contains(text(),"Suivant")]/@href'
        ).extract()
        if next_page:
            yield Request(next_page[0], callback=self.parse_without_captcha)

    def parse_profile(self, response):
        item = response.meta.get('item')

        email = response.xpath(
            '//a[contains(@href,"mailto")]/span/text()[contains(., "@")]'
        ).extract()
        if email:
            email = email[0].strip()
        else:
            return None
        cond_set(item, 'name',
                 response.xpath(
                     "//div[@class='profile-info']/div/div/span/text()"
                 ).extract(), string.strip)
        cond_set_value(item, 'email', email)
        cond_set_value(item, 'reviewer', response.url)
        cond_set_value(item, 'country', self.COUNTRY)

        return item
