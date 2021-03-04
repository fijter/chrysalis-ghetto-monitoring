import paho.mqtt.subscribe as subscribe
import datetime
import multiprocessing
import requests
from requests.exceptions import Timeout
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()    

confirmed_ms = {}

def test_msg(broker, port, timeout):
    try:
        msg = subscribe.simple('messages', hostname=broker, port=port, keepalive=timeout)
        return msg
    except Exception:
        time.sleep(timeout + 1)
        return False

def log_to_slack(message):
    slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    data = {
        'username': 'chrysalis-testnet',
        'channel': '#chrysalis-testnet-monitoring',
        'text': message
    }

    requests.post(slack_webhook, data=json.dumps(data))


def check_mqtt(broker='api.hornet-0.testnet.chrysalis2.com', port=1883, timeout=30):
    
    try:
        p = multiprocessing.Process(target=test_msg, kwargs={'broker': broker, 'port': port, 'timeout': timeout})
        p.start()
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            print('Timed out without receiving a message...')
            return (False, 'Timed out without receiving a message')
        else:
            return (True, None)

    except Exception as e:
        print("Something went wrong: %s" % e)
        return (False, 'Something went wrong: %s' % e)

def check_sync(api_base, milestone_max_diff=10, timeout=10):
    try:
        resp = requests.get('%s/api/v1/info' % api_base, timeout=timeout)
    except Timeout:
        return (False, 'API request timed out')
    
    if resp.status_code != 200:
        return (False, 'Status code %d returned instead of 200' % (resp.status_code))

    try:
        dat = resp.json()
    except:
        return (False, 'No JSON Returned by API')

    data = dat.get('data')

    if not data:
        return (False, 'Result JSON does not contain "data" key: %s' % data)

    lmi = data.get('latestMilestoneIndex')
    smi = data.get('solidMilestoneIndex')

    confirmed_ms[api_base] = smi

    if not lmi or not smi:
        return (False, 'Milestone indexes not returned in result body: %s' % data)

    if (lmi + milestone_max_diff) < smi:
        return (False, 'Out of sync by %d milestones' % (smi - lmi))


    return (True, None)

def test_endpoint(uri, test_mqtt=True, test_api=True):

    if test_mqtt:
        broker = uri.split('://')[1]
        success, message = check_mqtt(broker=broker, timeout=10)
        if not success:
            print('Failed MQTT test for %s' % broker)
            print(message)
            log_to_slack('MQTT test failed for %s: %s' % (broker, message))

    if test_api:
        success, message = check_sync(uri, timeout=10)
        if not success:
            print('Failed node API test')
            print(message)
            log_to_slack('API Test failed for %s: %s' % (uri, message))


if __name__ == '__main__':
    
    confirmed_ms = {}

    test_endpoint('https://api.lb-0.testnet.chrysalis2.com', test_mqtt=False)
    test_endpoint('https://api.coo.testnet.chrysalis2.com', test_mqtt=False)

    for i in range(4):
        uri = 'https://api.hornet-%d.testnet.chrysalis2.com' % i
        test_endpoint(uri)
    
    for host, ms in confirmed_ms.items():
        for ohost, ams in confirmed_ms.items():
            if (ms + 10) < ams:
                msg = '%s %s confirmed milestones behind on %s (%s/%s)' % (host, ams-ms, ohost, ms, ams)
                print(msg)
                log_to_slack('Node issue: %s' % (msg,))

