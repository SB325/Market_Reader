import time
import math
import requests
from requests.models import Response
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging
import pdb

# https://opentelemetry-python.readthedocs.io/en/latest/sdk/index.html

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
    def __init__(self, last_request_time: int = 0, rate_limit: int = 0.5):
        self.last_request_time = last_request_time
        self.rate_limit = rate_limit  # minimum period or 1/max rate per second. For edgar, limit is listed at 10/sec
        self.session = requests.Session()
        self.session.mount('http://', adapter)

    def get_last_request_time(self):
        return self.last_request_time
    
    def set_request_time(self):
        self.last_request_time = math.floor(time.time())*1000
        
    def wait_half_second(self):
        time_since_last_request = math.floor(time.time())*1000 - self.get_last_request_time()
        # if wait_time < 0s, set to 0s (no negatives, shouldn't be the case)
        wait_time = self.rate_limit-time_since_last_request
        if (wait_time < 0):
            wait_time = 0
        time.sleep(wait_time)
        
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
    pass