# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

class AmazonspiderPipeline(object):
    def process_item(self, item, spider):
        f = open(spider.file_name, 'a')
        f.write(json.dumps(dict(item)))
        f.close()
        return item
