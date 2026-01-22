import time
import math
import requests
from requests.models import Response
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging
import pdb
from uuid import uuid4
from kafka.kafka import KafkaProducer, KafkaConsumer
import json
# https://opentelemetry-python.readthedocs.io/en/latest/sdk/index.html

class distributed_delay_client():
    '''
    For ensuring that request rates are capped to a limit in distributed workloads, 
    distributed_delay_client will push a guid to the delay_queue server (dq) on a topic
    and wait for a response. 
    The dq will queue the guid and return them (pop and return) them in fifo order. 
    Each guid will be returned at a rate not to exceed a specified limit. Clients
    waiting for their guid to be returned will listen (consume) on the request topic until the 
    it arrives before proceeding. Best for rate limits below 10 requests per second.
    '''
    def __init__(self, 
                    delay_queue_topic: str,
                    ready_queue_topic: str,
                    max_rate_per_s: int = 10,
                ):
        self.period_s = 1/max_rate_per_s 
        self.topic = delay_queue_topic
        self.producer = KafkaProducer(
                    topic = delay_queue_topic,
                    clear_topic = False)
        self.consumer = KafkaConsumer(topic = [ready_queue_topic],
                        partition_messages = False,
                        commit_immediately = False)

    def wait(self):
        # send guid to kafka queue
        uuid = str(uuid4())
        self.producer.send(json.dumps({
                    'uuid': uuid, 
                    'period': self.period_s}), 
                    self.topic, 
                    use_redis = False
                )

        # wait for response
        done = False
        messages = []
        while not done:
            msg = self.consumer.recieve_once(use_redis = False)
            if msg:
                message = json.loads(msg)
                messages.append(message)
                if uuid in message['uuid']:
                    done = True
                    print(f"Message {uuid} found! Proceeding to send request.")
            else:
                done = True

        return

retry = Retry(
        total=3,
        backoff_factor=5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
logging.getLogger("urllib3").setLevel(logging.DEBUG)
adapter = HTTPAdapter(max_retries=retry)

class requests_util:
    '''
    requests_util is a clean, simple interface for requests get, post etc requests
    Requests_Util forces a time period between consecutive REST requests in order to comply with API rate limits.
    '''
    def __init__(self, 
            last_request_time: int = 0, 
            rate_limit: int = 0.5, 
            distributed: bool = False,
            delay_queue_topic: str = 'set_delay_topic',
            ready_queue_topic: str = 'set_ready_topic',
            ):
        self.last_request_time = last_request_time
        self.rate_limit = rate_limit  # minimum period or 1/max rate per second. For edgar, limit is listed at 10/sec
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.distributed = bool(delay_queue_topic)
        if distributed:
            self.ddc = distributed_delay_client(
                        delay_queue_topic = delay_queue_topic,
                        ready_queue_topic = ready_queue_topic,
                        max_rate_per_s = rate_limit,
                        )

    def get_last_request_time(self):
        return self.last_request_time
    
    def set_request_time(self):
        self.last_request_time = math.floor(time.time())*1000
        
    def wait_half_second(self):
        if not self.distributed:
            time_since_last_request = math.floor(time.time())*1000 - self.get_last_request_time()
            # if wait_time < 0s, set to 0s (no negatives, shouldn't be the case)
            wait_time = self.rate_limit-time_since_last_request
            if (wait_time < 0):
                wait_time = 0
            time.sleep(wait_time)
        else:
            self.ddc.wait()
        
    def get(self, url_in: str, params_dict: dict = {}, headers_in: dict = {}, stream_in: bool = False):
        self.wait_half_second()
        response = Response()
        response.code = "unknown"
        response.error_type = "unknown"
        response.status_code =500
        try:
            response = self.session.get(url=url_in, params=params_dict, headers=headers_in, stream=stream_in, timeout=10)
        except:
            print(f"GET Request for \n{response.url}\n Failed. {response.status_code}")
                
        self.set_request_time()    
        return response    

    def post(self, url_in: str, data_in: str = None, json_in: str = None, headers_in={}):
        if len(headers_in.keys()):
            response = self.session.post(url=url_in, data=data_in, json=json_in, headers=headers_in)
        else:
            response = self.session.post(url=url_in, data=data_in, json=json_in)

        if response.status_code != 200:
            print(f"Post Error! Code {response.status_code}: {response.reason}") 
        return response  
    
    def put(self, url_in: str, data_in: str, json_in: str = {}):
        response = self.session.put(url = url_in, data = data_in)
        return response
    
if __name__ == '__main__':
    url='https://www.sec.gov/files/company_tickers.json'
    header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
                'Accept-Encoding':'deflate', \
                'Host':'www.sec.gov'}
            
    requtil = requests_util(distributed = True)
    response = requtil.get(url_in = url, headers_in = header)
    pdb.set_trace()
