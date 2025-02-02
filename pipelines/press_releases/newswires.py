# Benzinga News API client
import pdb
import os
import sys
from dotenv import load_dotenv
import pdb 
sys.path.append("../../")
from util.requests_util import requests_util
from util.elastic.crud_elastic import crud_elastic
from util.elastic.models import news_article_model
from newswire_params import NewsAPIParams

load_dotenv(override=True, dotenv_path='newsapi_creds.env')  
key = os.getenv("BENZINGA_API_KEY")
webhook_dest = os.getenv("WEBHOOK_ENDPT")

url = "https://api.benzinga.com/api/v2/news"
webhook_url = "https://api.benzinga.com/api/v1/webhook/"
headers = {"accept": "application/json"}

crud = crud_elastic()
requests = requests_util()

class newswire():
    def __init__(self, key: str = key):
        self.key = key
        self.index = 'market_news'

    def get_news_history(self, params: NewsAPIParams):
        # Get news history queried by configs in NewsAPIParams
        try:
            querystring = {}
            querystring.update({"token":self.key})
            querystring.update(params)

            response = requests.get(url, headers_in=headers, params_dict=querystring)
        except Exception as e:
            print(f"Error: {e}")
        
        return response.json()

    def to_db(self, newsdata: news_article_model):
        # Push newsdata to Postgres DB
        try:
            crud.insert_document(index = self.index, document = newsdata)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    nw = newswire()