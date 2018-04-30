from flask import Flask
from flask import request
from time import sleep
from datetime import datetime, timedelta
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import os
from flask import Response
app = Flask(__name__)
executor = ThreadPoolExecutor(1)

# server settings
HOST = '127.0.0.1'
PORT = int(os.environ.get('PORT', 5000))
DEBUG_MODE = True
with open('../slack_supportbot_secrets.json') as json_load:
    json_struct = json.load(json_load)
    webhook = json_struct['webhook']

def sendMessageToSlack(string):
    header = {'Content-type':'application/json'}
    payload = {'text':string}
    print(payload)
    r = requests.post(webhook, json=payload, headers=header)
    print(r.text)
    return


# changes the responsibilities every 2 weeks
def changeResponsibility():
    with open('people.json', 'r+') as json_load:
        people_list = json.load(json_load)
        if len(people_list) > 0:
            people_list.append(people_list.pop(0)) 
            people_list.append(people_list.pop(0))
        print((people_list[0] if len(people_list) > 0 else 'Niemand ist') + ((' und ' + people_list[1] + ' sind') if len(people_list) > 1 else ' ist') + ' zurzeit für den Support zuständig!')
        sendMessageToSlack('<!everyone> ' + (people_list[0] if len(people_list) > 0 else 'Niemand ist') + ((' und ' + people_list[1] + ' sind') if len(people_list) > 1 else ' ist') + ' zurzeit für den Support zuständig!')
        json_load.seek(0)
        json_load.write(json.dumps(people_list))
        json_load.truncate()   
    return

def checkResponsibility():
    while True:
        with open('config.json', 'r+') as json_config:
            config = json.load(json_config)
            config_date = datetime.strptime(config['startdate'], '%d.%m.%Y')
            if config_date < datetime.now():
                while config_date < datetime.now():
                    config_date += timedelta(days=14)
                json_config.seek(0)
                json_config.write('{"startdate":"' + config_date.strftime('%d.%m.%Y') + '"}')
                json_config.truncate()
                changeResponsibility()
        sleep(5)
        return

# set up background thread to change responsibilities every 2 weeks and start API server 
executor.submit(checkResponsibility)
print('Backgroundthread started!')


# routing

@app.route('/addsupporter', methods=['POST'])
def addsupporter():
    with open('people.json', 'r+') as json_load:
        people_list = json.load(json_load)
        people_list.append(request.form['text'])
        json_load.seek(0)
        json_load.write(json.dumps(people_list))
        json_load.truncate()
    resp = Response(json.dumps({'text': request.form['text'] + ' wurde als Supporter hinzugefügt!', 'response_type':'in_channel'}))
    resp.headers['Content-type'] = 'application/json'
    return resp

@app.route('/currsupporter', methods=['POST'])
def currsupporter():
    with open('people.json', 'r') as json_load:
        people_list = json.load(json_load)
        print(people_list)
    resp = Response(json.dumps({'text': (people_list[0] if len(people_list) > 0 else 'Niemand ist')  + ((' und ' + people_list[1] + ' sind') if len(people_list) > 1 else ' ist') + ' zurzeit für den Support zuständig!' , 'response_type':'in_channel'}))
    resp.headers['Content-type'] = 'application/json'
    return resp

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, host=HOST, port=PORT)
