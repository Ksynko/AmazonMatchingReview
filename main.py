import os
import time
import random

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/get_data', methods=['POST'])
def add_task():
    print 'add_task'
    if request.method == 'POST':
        client_url = request.args.get('client_url', '')
        asins = request.args.get('products_asins', '')

        hash = random.getrandbits(128)
        file_name = '/tmp/'+str(hash)+'.json'

        command = "scrapy crawl amazon -a client_url='"+client_url+\
                  "' -a product_asins='"+asins+"' -a file_name='"+file_name+"'"

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
