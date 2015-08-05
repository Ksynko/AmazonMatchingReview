import os
import time
import random
import json

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
        client_url = request.args.get('client_url', '')
        asins = request.args.get('products_asins', '')
	if not client_url or not asins:
	    client_url = request.form.get('client_url', '')
            asins = request.form.get('products_asins', '')
	    if not client_url or not asins:    
	        return 'Not all parameters'
        hash = random.getrandbits(128)
        file_name = '/tmp/'+str(hash)+'.json'
	
	product_asins = {"asins": asins}	

        command = "cd /home/ubuntu/amazonmatchingreview/ && scrapy crawl amazon -a client_url='"+client_url+\
                  "' -a product_asins='"+json.dumps(product_asins)+"' -a file_name='"+file_name+"'"
	print command, '*'*40
        os.system(command)
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
