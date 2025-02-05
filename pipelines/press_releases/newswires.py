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

requests = requests_util()

class newswire():
    def __init__(self, crud: crud_elastic, key: str = key):
        self.key = key
        self.index = 'market_news'
        self.crud = crud
        # check if index exists, create if it doesn't
        if not self.crud.get_index(index="market_news"):
            self.crud.create_index(new_index = self.index,
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
            self.crud.insert_document(index = self.index, document = newsdata)
        except Exception as e:
            print(f"Error: {e}")

    def to_db_bulk(self, ticker: str, newsdata: List[news_article_model]):
        # Push newsdata to elastic DB
        for article in newsdata:
            article.update({'ticker': ticker})
        try:
            self.crud.bulk_insert_documents(index=self.index, body = newsdata)
        except Exception as e:
            print(f"Error: {e}")

    def search_ticker(self, 
                index: str, 
                ticker: str,
                ):
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
        resp = {}
        try:
            # cannot perform exact match, so match_all and return latest
            query = {"match_all": {}}
            resp = self.crud.client.search(index=index, 
                                           query=query, 
                                           pretty=True, 
                                           source={"includes":["source.created", "source.ticker"]}, 
                                           sort=[{"created": {"order": "desc" }}],
                                           size=1
                                           )
            print(f"Got {resp['hits']['total']['value']} Hits.")
            
        except Exception as e:
            print(f"Error: {e}")

        return resp
    
    def get_latest_news_from_ticker(self, ticker: str):
        # self.crud.client.search(index="market_news", query={"query_string": {"query": "Apple"}}, source={"includes":["source.created"]}, sort=[{"source.created": {"format": "strict_date_optional_time_nanos" }}])
        val = self.search_ticker(index=self.index, ticker=ticker)
        if val:
            nhits = val['hits']['total']['value']
            
            if nhits:
                dates = [dat['_source']['source']['created'] for dat in val['hits']['hits']]
                date_format = "%a, %d %b %Y %H:%M:%S %z"
                latest_date = datetime.strptime(min(dates), date_format)
            else:
                return "2020-01-01"
        else:
            return "2020-01-01"
        return latest_date.strftime("%Y-%m-%d")
    
if __name__ == "__main__":
    nw = newswire()