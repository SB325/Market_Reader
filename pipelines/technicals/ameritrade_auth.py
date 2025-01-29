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

import os.path
sys.path.append('../../util/')
from requests_util import requests_util
from dotenv import load_dotenv

load_dotenv(override=True, dotenv_path='tech_creds.env')  
APP_KEY = os.getenv("APP_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")
RESOURCE_URL = os.getenv("RESOURCE_URL")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

class schwab_auth(requests_util):
    def __init__(self):
        requests_util.__init__(self)
        self.refresh_token = BEARER_TOKEN
        self.callback_url = CALLBACK_URL
        self.app_key = APP_KEY
        self.resource_url = RESOURCE_URL
        # get from database instead of filesystem
        self.expiration = 0
    
    def post_req(self, url, params, headers={}):
        self.refresh()
        if len(headers.keys())>0:
            headers['Authorization']='Bearer ' + self.access_token
        self.post(url,params,*headers)
        
    def get_req(self, url, params,headers):
        self.refresh()
        headers['Authorization']='Bearer ' + self.access_token
        response = self.get(url,params,headers)
        if not response.ok:
            raise Exception('GET Request failed.')
        return self.get(url,params,headers)
    
    def refresh(self):
        now = math.floor(time.time())
        if (self.expiration<(now+60)):
            self.get_access_token()

    def get_access_token(self):
        url = self.resource_url
        data_dict = {'grant_type' :'refresh_token', \
                    'refresh_token' : self.refresh_token, \
                    'client_id' : self.consumer_key}
        reply = self.post(url, data_dict)
        
        if not reply.ok:
            print('Authentication Failed! {} Failed with {} code {}'.format(reply.request, reply.reason, reply.status_code))
            assert False
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire. store in db
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])
        # store in db
        self.access_token = replyjson['access_token']

    def get_refresh_token(self):
        # After logging into auth.tdameritrade.com/oauth, copy the reply url
        # into tokens\refresh_token.txt before running tda_auth.py.
        # get_refresh_token() will take care of the rest.
        url = self.resource_url
        raw_code=self.refresh_token
        code = raw_code[raw_code.find('code=')+5:]
        code = unquote(code,encoding='utf-8').replace('\n','')
        # refresh token at this point is merely the auth code needed to create
        # new tokens.
        data_dict = {'grant_type' :'authorization_code', \
                    'access_type' : 'offline', \
                    'code' : code, \
                    'client_id' : self.consumer_key, \
                    'redirect_uri' : self.callback_url}
        reply = self.post(url, data_dict)
        
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
        fid = open(homepath + 'tokens/access_token.txt','w')
        fid.write(self.access_token)
        fid.close()
        fid = open(homepath + 'tokens/refresh_token.txt','w')
        fid.write(self.refresh_token)
        fid.close()