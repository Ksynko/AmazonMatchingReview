import string
import json

from scrapy.http import Request, FormRequest
from scrapy.spider import Spider
from scrapy.log import ERROR, WARNING, INFO, DEBUG

from AmazonSpider.items import ReviewItem
from __init__ import cond_set, cond_set_value

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
    name = 'amazon_reviewer'
    allowed_domains = ["amazon.com"]
    start_urls = ['https://www.amazon.com/review/top-reviewers']

    MAX_RETRIES = 3

    user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) Gecko'
                  '/20100101 Firefox/35.0')

    page = 1

    def __init__(self,
                 captcha_retries='10',
                 *args, **kwargs):

        super(AmazonSpider, self).__init__(*args, **kwargs)

        self.captcha_retries = int(captcha_retries)
        self._cbw = CaptchaBreakerWrapper()

    # def make_requests_from_url(self, _):
    #     """This method does not apply to this type of spider so it is overriden
    #     and "disabled" by making it raise an exception unconditionally.
    #     """
    #     raise AssertionError("Need a search term.")

    def parse(self, response):
        if self._has_captcha(response):
            result = self._handle_captcha(response, self.parse)
        else:
            result = self.parse_without_captcha(response)
        return result

    def parse_without_captcha(self, response):
        links = response.xpath('//td[@class="img"]/a[1]/@href').extract() [:10]
        for link in links:
            yield Request('http://www.amazon.com'+link,
                          callback=self.parse_email)

        next_page = response.xpath('//a[contains(text(),"Next")]/@href').extract()
        # if next_page:
        #     yield Request(next_page[0],callback=self.parse_without_captcha)

    def parse_email(self, response):
        item = ReviewItem()

        email = response.xpath(
                     '//a[contains(@href,"mailto")]/span/text()'
                 ).extract()
        if email:
            email = email[0].strip()
        cond_set_value(item, 'email', email)
        cond_set_value(item, 'reviewer', response.url)

        return item

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
