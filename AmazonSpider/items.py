# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class AmazonspiderItem(Item):
    client_url = Field()
    asins = Field()
    error_message = Field()


class ReviewItem(Item):
    reviewer = Field()
    email = Field()
