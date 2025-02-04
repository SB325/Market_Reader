import time
import math
import requests
from requests.models import Response
import pdb

class requests_util:
    '''
    requests_util is a clean, simple interface for requests get, post etc requests
    Requests_Util forces a time period between consecutive REST requests in order to comply with API rate limits.
    '''
    def __init__(self, last_request_time: int = 0, access_token: str = '', rate_limit: int = 1):
        self.last_request_time = last_request_time
        self.access_token = access_token
        self.rate_limit = rate_limit  # minimum period or 1/max rate per second. For edgar, limit is listed at 10/sec
        
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
        try:
            response = requests.get(url=url_in, params=params_dict, headers=headers_in, stream=stream_in, timeout=5)
        except:
            response = Response()
            response.code = "expired"
            response.error_type = "expired"
            response.status_code = 408
            print(f"GET Request for \n{response.url}\n Failed. {response.status_code}")
                
        self.set_request_time()    
        return response    

    def post(self, url_in: str, data_in: str = None, json_in: str = None, headers_in={}):
        if len(headers_in.keys()):
            response = requests.post(url=url_in, data=data_in, json=json_in, headers=headers_in)
        else:
            response = requests.post(url=url_in, data=data_in, json=json_in)

        if response.status_code != 200:
            print(f"Post Error! Code {response.status_code}: {response.reason}") 
        return response  
    
    def put(self, url_in: str, data_in: str, json_in: str = {}):
        response = requests.put(url = url_in, data = data_in)
        return response