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
sys.path.append('../../util/')
from requests_util import requests_util
from replace_line_env import replace
from dotenv import load_dotenv
from urllib.parse import unquote

creds_file = 'tech_creds.env'
load_dotenv(override=True, dotenv_path=creds_file)  
APP_KEY = os.getenv("APP_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")
RESOURCE_URL = os.getenv("RESOURCE_URL")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

class schwab_auth(requests_util):
    def __init__(self):
        requests_util.__init__(self)
        self.callback_url = CALLBACK_URL
        self.app_key = APP_KEY

        self.access_token = ACCESS_TOKEN  # For Bearer Authorization
        self.refresh_token = REFRESH_TOKEN
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
                    'client_id' : self.app_key}
        
        reply = self.post(url, data_dict)
        pdb.set_trace()

        if not reply.ok:
            print('Authentication Failed! {} Failed with {} code {}'.format(reply.request, reply.reason, reply.status_code))
            assert False
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire. store in db
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])
        replace(creds_file, f"REFRESH_TOKEN={self.access_token}",
                    f"REFRESH_TOKEN={replyjson['access_token']}")
        self.access_token = replyjson['access_token']

    def get_refresh_token(self):
        # After logging into auth.schwabapi.com/oauth, copy the reply url
        # into tokens\refresh_token.txt before running tda_auth.py.
        # get_refresh_token() will take care of the rest.
        url = self.resource_url
        raw_code=self.refresh_token
        pdb.set_trace()
        code = raw_code[raw_code.find('code=')+5:]
        code = unquote(code,encoding='utf-8').replace('\n','')
        # refresh token at this point is merely the auth code needed to create
        # new tokens.
        data_dict = {'grant_type' :'authorization_code', \
                    'access_type' : 'offline', \
                    'code' : code, \
                    'client_id' : self.app_key, \
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
        with open(creds_file) as old_file:
            for line in old_file:
                if 'REFRESH_TOKEN=' in line:
                    oldRefreshToken = line.split('=')[2]
                if 'ACCESS_TOKEN' in line:
                    oldAccessToken = line.split('=')[2]
        
        replace(creds_file, f"REFRESH_TOKEN={oldRefreshToken}",
                    f"REFRESH_TOKEN={self.refresh_token}")
        
        replace(creds_file, f"ACCESS_TOKEN={oldAccessToken}",
                    f"ACCESS_TOKEN={self.access_token}")