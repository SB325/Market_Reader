###############################################################
#   Schwab Ameritrade Authorization class
###############################################################
# This class interface wraps all Schwab trader endpoint calls in
#   a way that manages the refreshing and re-authorization of keys
#   so that it is an afterthought during development.

from pprint import pprint
import os
import sys
import time 
import math
import json
import pdb
from os import fdopen
import os.path
import base64
sys.path.append('../../')
from util.requests_util import requests_util
from util.replace_line_env import replace
from dotenv import load_dotenv
from urllib.parse import unquote

creds_file = 'tech_creds.env'
load_dotenv(override=True, dotenv_path=creds_file)  
APP_KEY = os.getenv("APP_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")
RESOURCE_URL = os.getenv("RESOURCE_URL")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_SECRET = os.getenv("SECRET")

class schwab_auth(requests_util):
    callback_url = CALLBACK_URL
    app_key = APP_KEY
    access_token = ACCESS_TOKEN  # For Bearer Authorization
    refresh_token = REFRESH_TOKEN
    resource_url = RESOURCE_URL
    app_secret = APP_SECRET
    # get from database instead of filesystem
    expiration = 0
    
    def __init__(self):
        requests_util.__init__(self)
        
    def post_request(self, url, params, headers={}):
        self.refresh()
        headers['Authorization']='Bearer ' + self.access_token
        headers["Content-Type"]="application/json"
        self.post(url_in=url, params_dict=params, headers_in=headers)
        
    def get_request(self, url, params={}, headers={}):
        self.refresh()
        headers['Authorization']='Bearer ' + self.access_token
        headers["Content-Type"]="application/json"
        params.update({'apikey': self.app_key})
        response = self.get(url_in=url, params_dict=params, headers_in=headers)
        if not response.ok:
            raise Exception(f'GET Request failed.\n{response.reason}')
        return response
    
    def refresh(self):
        # Refresh access token if it is expires or will expire 
        # within the next minute.
        now = math.floor(time.time())
        if (self.expiration<(now+60)):
            self.get_access_token()

    def get_access_token(self):
        headers = { 
                    'Authorization' : f'Basic {self.get_base_64_credentials()}',
                    'Content-Type' : 'application/x-www-form-urlencoded', 
                }
        data_dict = {
                    'grant_type' :'refresh_token', 
                    'refresh_token' : self.refresh_token, 
                }
        
        reply = self.post(url_in=self.resource_url, headers_in=headers, data_in=data_dict)

        if not reply.ok:
            print('Authentication Failed! {} Failed with {} code {}'.format(reply.request, reply.reason, reply.status_code))
            assert False
            
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire. store in db
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])
        replace(creds_file, f"ACCESS_TOKEN={self.access_token}",
                    f"ACCESS_TOKEN={replyjson['access_token']}")
        self.access_token = replyjson['access_token']
        
    def get_refresh_token(self):
        # After logging into auth.schwabapi.com/oauth, copy the reply url
        # into tech_creds.env before running schwab_auth.py.
        # get_refresh_token() will take care of the rest. Code expires quickly,
        # so run soon after generating.
        raw_code=self.refresh_token
        
        # code = raw_code[raw_code.find('code=')+5:]
        code = f"{raw_code[raw_code.index('code=') + 5: raw_code.index('%40')]}@"
        code = unquote(code,encoding='utf-8').replace('\n','')

        # refresh token at this point is merely the auth code needed to create
        # new tokens.
        base64_credentials = self.get_base_64_credentials()
        data_dict = {
                'grant_type' :'authorization_code', 
                'code' : code, 
                'redirect_uri' : self.callback_url
                }
        headers = { 
                    'Authorization' : f'Basic {base64_credentials}',
                    'Content-Type' : 'application/x-www-form-urlencoded', \
                    }
        
        reply = self.post(url_in=self.resource_url, 
                          data_in = data_dict, 
                          headers_in = headers
                    )
        
        if not reply.ok:
            print('Authentication Failed!')
            print(f"{reply.request} Failed with {reply.reason} code:{reply.status_code}")
            print(f"full response: \n{json.loads(reply.text)}")
            print(f"{data_dict}")
            assert False
            
        print('Successfully authenticated tokens!')
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])

        self.access_token = replyjson['access_token']
        self.refresh_token = replyjson['refresh_token']
        # write to db instead
        with open(creds_file) as old_file:
            for line in old_file:
                if 'REFRESH_TOKEN=' in line:
                    oldRefreshToken = line
                if 'ACCESS_TOKEN' in line:
                    oldAccessToken = line
        
        replace(creds_file, oldRefreshToken.replace('\n',''),
                    f"REFRESH_TOKEN={self.refresh_token}")

        replace(creds_file, f"ACCESS_TOKEN={oldAccessToken}",
                    f"ACCESS_TOKEN={self.access_token}")
        
    def get_base_64_credentials(self):
        credentials = f"{self.app_key}:{self.app_secret}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8") 

if __name__ == '__main__':
    auth = schwab_auth()
    auth.get_access_token()
    pdb.set_trace()