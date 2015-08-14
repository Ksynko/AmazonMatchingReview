from scrapy.http import Request, FormRequest
from scrapy.spider import Spider
from scrapy.log import ERROR, WARNING, INFO, DEBUG


def identity(x):
    return x

def cond_set(item, key, values, conv=identity):
    """Conditionally sets the first element of the given iterable to the given
    dict.

    The condition is that the key is not set in the item or its value is None.
    Also, the value to be set must not be None.
    """
    try:
        if values:
            value = next(iter(values))
            cond_set_value(item, key, value, conv)
    except StopIteration:
        pass


def cond_set_value(item, key, value, conv=identity):
    """Conditionally sets the given value to the given dict.

    The condition is that the key is not set in the item or its value is None.
    Also, the value to be set must not be None.
    """
    if item.get(key) is None and value is not None and conv(value) is not None:
        item[key] = conv(value)

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


class AmazonBaseClass(Spider):
    def __init__(self,
                 captcha_retries='10',
                 *args, **kwargs):

        super(AmazonBaseClass, self).__init__(*args, **kwargs)

        self.captcha_retries = int(captcha_retries)
        self._cbw = CaptchaBreakerWrapper()

    def parse(self, response):
        if self._has_captcha(response):
            result = self._handle_captcha(response, self.parse)
        else:
            result = self.parse_without_captcha(response)
        return result

    def parse_links(self, response):
        """
        Handles parsing of a top reviewers page.
        :param response:
        :return: ReviewItem's with Rank
        """
        raise NotImplementedError

    def parse_profile(self, response):
        """
        Handles parsing of a reviewer profile page.
        :param response:
        :return: ReviewItem's with Email, Name and Country
        """
        raise NotImplementedError

    def parse_without_captcha(self, response):
        if not self._has_captcha(response):
            res = self.parse_links(response)
            for i in res:
                yield i
        else:
            result = self._handle_captcha(response, self.parse_without_captcha)
            yield result

    def parse_email(self, response):
        if not self._has_captcha(response):
            result = self.parse_profile(response)
            if result:
                return result
        else:
            result = self._handle_captcha(response, self.parse_email)
            return result

    # Captcha handling functions.
    def _has_captcha(self, response):
        return 'images-amazon.com/captcha/' in response.body_as_unicode()

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
