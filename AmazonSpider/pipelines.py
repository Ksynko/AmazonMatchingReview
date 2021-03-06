# -*- coding: utf-8 -*-
import json, httplib


class AmazonspiderPipeline(object):
    def process_item(self, item, spider):
        if spider.name == 'amazon':
            f = open(spider.file_name, 'a')
            f.write(json.dumps(dict(item)))
            f.close()
        else:
            connection = httplib.HTTPSConnection('api.parse.com', 443)
            connection.connect()
            connection.request(
                'POST', '/1/classes/TopAmazonReviewers',
                json.dumps({
                    "name": item.get('name', ''),
                    "emailAddress": item.get('email', ''),
                    "rank": item.get('rank', ''),
                    "country": item.get('country', '')}),
                {
                    "X-Parse-Application-Id": "efPfMd7LXWV4I2HQ7HsUBnQzkuEj6UrYjbD07Scm",
                    "X-Parse-REST-API-Key": "5PrqGxeHBTe5zPYG7atNebIqTqGENp7AUShSIkUr",
                    "Content-Type": "application/json"
                })
            results = json.loads(connection.getresponse().read())
            connection.close()
            print results
        return item
