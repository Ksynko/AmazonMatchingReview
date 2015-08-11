import os
import time
import random
import json
import re

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/hello')
def hello():
    return 'Hello World!'

@app.route('/get_data', methods=['POST'])
def add_task():
    print 'add_task'
    if request.method == 'POST':
        try:
#	    print '!'*100
#            print request.is_json
#            print dir(request)
            print request.data
	    print request.form
            print type(request.data)
#            print request.json
#            j = request.get_json(force=True)
#            print j
        except Exception as e:
            print e
        client_url = request.args.get('client_url', '')
        asins = request.args.get('products_asins', '')
	if not client_url or not asins:
	    client_url = request.form.get('client_url', '')
            asins = request.form.get('products_asins', '')
	    if not client_url or not asins:
                try:
                    data = json.loads(request.data)
                    client_url = data['client_url']
                    asins = data['products_asins']
                except Exception as e:
                    print e
                if not client_url or not asins:
	            return 'Not all parameters'

        regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not re.match(regex, client_url):
            return "Sorry, we receive incorect url '%s', please check it" % client_url

        hash = random.getrandbits(128)
        file_name = '/tmp/'+str(hash)+'.json'
	
	product_asins = {"asins": asins}	

        command = "cd /home/ubuntu/amazonmatchingreview/ && scrapy crawl amazon -a client_url='"+client_url+\
                  "' -a product_asins='"+json.dumps(product_asins)+"' -a file_name='"+file_name+"'"
	print command, '*'*40
	try:
            os.system(command)
	except:
	    return 'Invalid parametrs, please check it'
        result = ''
        while True:
            try:
                f = open(file_name, 'r')
                result = f.read()
                f.close()
                os.remove(file_name)
                break
            except:
                time.sleep(0.5)
                pass

        return result

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
