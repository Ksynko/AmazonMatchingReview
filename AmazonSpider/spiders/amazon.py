import string
import json

from scrapy.http import Request, FormRequest
from scrapy.spider import Spider
from scrapy.log import ERROR, WARNING, INFO, DEBUG

from AmazonSpider.items import AmazonspiderItem

try:
    from captcha_solver import CaptchaBreakerWrapper
except Exception as e:
    print '!!!!!!!!Captcha breaker is not available due to: %s' % e

    class CaptchaBreakerWrapper(object):
        @staticmethod
        def solve_captcha(url):
            msg("CaptchaBreaker in not available for url: %s" % url,
                level=WARNING)
            return None

class AmazonSpider(Spider):
    name = 'amazon'
    allowed_domains = ["amazon.com"]
    start_urls = []
    handle_httpstatus_list = [404]
    MAX_RETRIES = 3

    user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) Gecko'
                  '/20100101 Firefox/35.0')

    page = 1

    def __init__(self,
                 url_formatter=None,
                 client_url=None,
                 file_name=None,
                 product_asins=None,
                 captcha_retries='10',
                 *args, **kwargs):

        self.SEARCH_URL = client_url
        super(AmazonSpider, self).__init__(*args, **kwargs)

        if file_name:
            self.file_name = file_name

        if url_formatter is None:
            self.url_formatter = string.Formatter()
        else:
            self.url_formatter = url_formatter

        product_asins = json.loads(product_asins)
        self.product_asins = product_asins['asins']

        self.captcha_retries = int(captcha_retries)
        self._cbw = CaptchaBreakerWrapper()

    def make_requests_from_url(self, _):
        """This method does not apply to this type of spider so it is overriden
        and "disabled" by making it raise an exception unconditionally.
        """
        raise AssertionError("Need a search term.")

    def start_requests(self):
        """Generate Requests from the SEARCH_URL and the search terms."""
        meta = {'asins': self.product_asins}
        yield Request(self.SEARCH_URL,
                      meta=meta)

    def parse(self, response):
        if self._has_captcha(response):
            result = self._handle_captcha(response, self.parse)
        else:
            result = self.parse_without_captcha(response)
        return result

    def parse_without_captcha(self, response):
        item = AmazonspiderItem()
        if response.status == 404:
            item['error_message'] = '404 Invalid URL'
            return item
        item['client_url'] = response.url
        meta = response.meta.copy()
        meta['item'] = item
        reviews_url = response.xpath(
            '//a/span[contains(text(), "Reviews")]/../@href |'
            '//a[@class="a-link-normal"]/@href[contains(.,"member-reviews")]'
        ).extract()

        if reviews_url:
            reviews_url = 'http://www.amazon.com' + reviews_url[0]

            return Request(reviews_url, meta=meta,
                           callback=self.parse_reviews)
        else:
            item['error_message'] = 'Amazon blocked, try again'
            return item

    def parse_reviews(self, response):
        print 'PARSE REVIEWS'
        products_asins = response.meta.get('asins')
        item = response.meta.get('item')

        review_asins = response.xpath(
            '//table[@class="small"]/tr/td/b/a/@href').re('dp/(.*)/ref')
        find_asins = []
        for asin in review_asins:
            if asin in products_asins:
                find_asins.append(asin)

        if 'asins' not in item.keys():
            item['asins'] = find_asins
        else:
            item['asins'].extend(find_asins)

        self.page += 1
        next_page_url = response.xpath(
            '//td[@class="small"]/b/a[contains(@href,"page=' +str(self.page)
            + '")]/@href').extract()
        if next_page_url:
            next_page_url = 'http://www.amazon.com' + next_page_url[0]

            meta = response.meta.copy()
            meta['item'] = item
            yield Request(next_page_url, meta=meta,
                          callback=self.parse_reviews)
        else:
            yield item

    # Captcha handling functions.
    def _has_captcha(self, response):
        return '.images-amazon.com/captcha/' in response.body_as_unicode()

    def _solve_captcha(self, response):
        forms = response.xpath('//form')
        assert len(forms) == 1, "More than one form found."

        captcha_img = forms[0].xpath(
            '//img[contains(@src, "/captcha/")]/@src').extract()[0]

        self.log("Extracted capcha url: %s" % captcha_img, level=DEBUG)
        return self._cbw.solve_captcha(captcha_img)

    def _handle_captcha(self, response, callback):
        captcha_solve_try = response.meta.get('captcha_solve_try', 0)
        url = response.url
        self.log("Captcha challenge for %s (try %d)."
                 % (url, captcha_solve_try),
                 level=INFO)

        captcha = self._solve_captcha(response)

        if captcha is None:
            self.log(
                "Failed to guess captcha for '%s' (try: %d)." % (
                    url, captcha_solve_try),
                level=ERROR
            )
            result = None
        else:
            self.log(
                "On try %d, submitting captcha '%s' for '%s'." % (
                    captcha_solve_try, captcha, url),
                level=INFO
            )
            meta = response.meta.copy()
            meta['captcha_solve_try'] = captcha_solve_try + 1
            result = FormRequest.from_response(
                response,
                formname='',
                formdata={'field-keywords': captcha},
                callback=callback,
                dont_filter=True,
                meta=meta)

        return result
