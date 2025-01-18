# Benzinga News API client
import pdb
import os
import sys
from dotenv import load_dotenv
import pdb 
os.path('../../')
from util.requests_util import requests_util
from util.db.models.news import News as NewsTable
from api_headers import NewsAPIParams
from util.crud import crud as crud

load_dotenv(override=True, dotenv_path='newsapi_creds.env')  
key = os.getenv("BENZINGA_API_KEY")
webhook_dest = os.getenv("WEBHOOK_ENDPT")

url = "https://api.benzinga.com/api/v2/news"
webhook_url = "https://api.benzinga.com/api/v1/webhook/"
headers = {"accept": "application/json"}

requests = requests_util()
crud_util = crud()

class newswire():
    def __init__(self, key: str = key):
        self.key = key

    def get_news_history(self, params: NewsAPIParams):
        # Get news history queried by configs in NewsAPIParams
        querystring = {"token":self.key}.update(params.model_dump())
        response = requests.get(url, headers=headers, params=querystring)

        return response.json()

    def get_news_webhook(self):
        # Get news webhook
        querystring = {"version":"webhook/v1", "kind":"News/v1", "destination": webhook_dest}
        response = requests.get(webhook_url, headers=headers, params=querystring)

        return response.json()

    def to_db(self, newsAPIResponse):
        # Push newsdata to Postgres DB
        await crud_util.insert_rows(NewsTable, df)