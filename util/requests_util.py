import time
import math
import requests

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
        # TDAPI requests are limited to 120 requests per minute
        # SNAPI requests may/may not have same limitation.
        time_since_last_request = math.floor(time.time())*1000 - self.get_last_request_time()
        # if wait_time < 0s, set to 0s (no negatives, shouldn't be the case)
        wait_time = self.rate_limit-time_since_last_request
        if (wait_time < 0):
            wait_time = 0
        time.sleep(wait_time)
        
    def get(self, url_in: str, params_dict: dict = {}, headers_in: dict = {}):
        self.wait_half_second()
        response = requests.get(url=url_in, params=params_dict, headers=headers_in)
        
        if not response.ok:
            print(f"GET Request for \n{response.url}\n Failed. {response.status_code}")
                
        self.set_request_time()    
        return response    

    def post(self, url_in, data_in, headers_in={}):
        if len(headers_in.keys()):
            response = requests.post(url=url_in, data=data_in, headers=headers_in)
        else:
            response = requests.post(url=url_in, data=data_in)

        if response.status_code != 200:
            print(f"Post Error! Code {response.status_code}: {response.reason}") 
            raise Exception()
        return response  