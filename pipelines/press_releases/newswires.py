# Benzinga News API client
import pdb
import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__)))
from util.requests_util import requests_util
from util.elastic.crud_elastic import crud_elastic
from util.elastic.models import news_article_model, news_article_mapping
from util.time_utils import posix_to_datestr
from newswire_params import NewsAPIParams
from typing import List
from elasticsearch.helpers import bulk

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
        if not self.crud.client.indices.exists(index="market_news"):
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
            if not response.ok: #"json" in dir(response):
                pdb.set_trace()
        except:
            #except Exception as e:
            print(f"Error: {e}")
            pdb.set_trace()

        return response.json()

    def to_db(self, ticker: str, newsdata: news_article_model):
        # Push newsdata to elastic DB
        newsdata.update({'ticker': ticker})
        try:
            ret = self.crud.client.index(index = self.index, document = newsdata)
        except Exception as e:
            print(f"Error: {e}")
        return ret

    def to_db_bulk(self, ticker: str, newsdata: List[news_article_model]):
        try:
            ### **** Client Bulk Method *******
            operations=[]
            ret = None
            # Push newsdata to elastic DB
            for article in newsdata:
                operations.append( 
                            {
                                "_index": self.index,
                                "_id": article['id'],
                                "_source": article
                            }
                )
            # pdb.set_trace()
            ret = bulk(self.crud.client, actions=operations)

            ### ** Helper Bulk Method *****
            #ret = self.crud.bulk_insert_documents(self.index, newsdata)
            
        except Exception as e:
            print(f"Error: {e}")
        return ret
    

    def search_ticker_match(self, 
                index: str, 
                ticker: str,
                ):
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
        resp = {}
        try:
            # self.crud.client.indices.refresh(index=self.index)
            resp = self.crud.client.search(index=index, 
                                           ignore_unavailable=True,
                                           query={"match": {'ticker': {'query': ticker}}},
                                           aggs={
                                                "tickerfilt" : {
                                                    "terms": {
                                                        "field": "ticker"
                                                    },
                                                    "aggs":{
                                                            "latest_date": {
                                                                "max": {
                                                                    "field": "created"
                                                                }
                                                            }
                                                    },
                                                }
                                            }
                                           
                                           )
            print(f"Got {resp['hits']['total']['value']} Hits.")
            # pdb.set_trace()
            
        except Exception as e:
            raise  Exception(f"Error: {e}")

        return resp
    
    def search_ticker(self, 
                index: str, 
                ticker: str,
                conditional: str = 'lte', # or 'gte'
                query_on_key: str = '',
                query_on_val: list = None
                ):
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
        resp = {}
        try:
            if query_on_key:
                assert query_on_val, "Missing value for -query_on_val-"
                query = {'bool': {'must': [
                                {"term": {'ticker': ticker}},
                                {"range": {query_on_key: {'gte': query_on_val[0],
                                                          'lte': query_on_val[1]
                                                        }
                                            }
                                }
                            ]
                        }
                }
            else:
                query = {"match": {'ticker': {'query': ticker}}}
            # self.crud.client.indices.refresh(index=self.index)
            resp = self.crud.client.search(index=index, 
                                           ignore_unavailable=True,
                                           query=query,
                                           size=10_000,
                                           request_timeout=30,
                                           sort=[
                                                    {
                                                        "created": {
                                                            "order": "desc"
                                                        }
                                                    },
                                                    "_score"
                                                ]
                                           )
            print(f"Got {resp['hits']['total']['value']} Hits.")
            # pdb.set_trace()
            
        except Exception as e:
            raise  Exception(f"Error: {e}")

        return resp
    
    def get_latest_news_from_ticker(self, ticker: str, default_latest: str="2020-01-01"):
        latest_dates = {'*': default_latest}
        val = self.search_ticker_match(index=self.index, ticker=ticker)
        if val.raw.get('aggregations', None): 
            buckets = val.raw['aggregations']['tickerfilt']['buckets']
            if buckets:
                latest_dates = {}
                [ latest_dates.update({val['key'] : posix_to_datestr(int(val['latest_date']['value'])) } ) 
                            for val in buckets ]
        
        return latest_dates
    
if __name__ == "__main__":
    nw = newswire()
