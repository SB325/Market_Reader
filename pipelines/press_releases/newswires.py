# Benzinga News API client
import pdb
import os
import sys
from dotenv import load_dotenv
import pdb 
sys.path.append("../../")
from util.requests_util import requests_util
from util.elastic.crud_elastic import crud_elastic
from util.elastic.models import news_article_model, news_article_mapping
from newswire_params import NewsAPIParams
from typing import List
from datetime import datetime

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
        # check if index exists, create if it doesn't
        if not crud.get_index(index="market_news"):
            crud.create_index(new_index = self.index,
                              new_mapping = news_article_mapping,
                        )

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

    def to_db(self, ticker: str, newsdata: news_article_model):
        # Push newsdata to elastic DB
        newsdata.update({'ticker': ticker})
        try:
            crud.insert_document(index = self.index, document = newsdata)
        except Exception as e:
            print(f"Error: {e}")

    def to_db_bulk(self, ticker: str, newsdata: List[news_article_model]):
        # Push newsdata to elastic DB
        for article in newsdata:
            article.update({'ticker': ticker})
        try:
            crud.bulk_insert_documents(index=self.index, body = newsdata)
        except Exception as e:
            print(f"Error: {e}")
            
    def search_ticker(self, ticker: str):
        return crud.search_ticker(index=self.index, ticker=ticker)

    def get_latest_news_from_ticker(self, ticker: str):
        val = self.search_ticker(ticker)
        nhits = val['hits']['total']['value']
        
        if nhits:
            dates = [dat['_source']['source']['created'] for dat in val['hits']['hits']]
            date_format = "%a, %d %b %Y %H:%M:%S %z"
            latest_date = datetime.strptime(min(dates), date_format)
        else:
            return "2020-01-01"
        return latest_date.strftime("%Y-%m-%d")
    
if __name__ == "__main__":
    nw = newswire()