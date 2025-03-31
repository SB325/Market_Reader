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
                print(f"Response Failed: {querystring}")
        except BaseException as e:
            print(f"Error: {e}")

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
            [news.update({'ticker': ticker}) for news in newsdata]

            ### **** Client Bulk Method *******
            operations=[]
            ret = None
            # Push newsdata to elastic DB
            # for article in newsdata:
            #     operations.append( 
            #                 {
            #                     "_index": self.index,
            #                     "_id": article['id'],
            #                     "_source": article
            #                 }
            #     )
            # pdb.set_trace()
            # ret = bulk(self.crud.client, actions=operations)

            ### ** Helper Bulk Method *****
            ret = self.crud.bulk_insert_documents(self.index, newsdata)
            
        except Exception as e:
            print(f"Error: {e}")
        return ret
    

    # def search_ticker_match(self, 
    #             index: str, 
    #             ticker: str,
    #             ):
    #     # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
    #     resp = {}
    #     try:
    #         # self.crud.client.indices.refresh(index=self.index)
    #         resp = self.crud.client.search(index=index, 
    #                                        ignore_unavailable=True,
    #                                        query={"match": {'ticker': {'query': ticker}}},
    #                                        aggs={
    #                                             "tickerfilt" : {
    #                                                 "terms": {
    #                                                     "field": "ticker"
    #                                                 }
    #                                                 # "aggs":{
    #                                                 #         "latest_date": {
    #                                                 #             "max": {
    #                                                 #                 "field": "created"
    #                                                 #             },
    #                                                 #             "terms": {
    #                                                 #                 "field": "_id"
    #                                                 #             }
    #                                                 #         }
    #                                                 # }
                                                    
    #                                             }
    #                                        },
    #                                         sort=[
    #                                             {
    #                                                 "created": {
    #                                                     "order": "desc"
    #                                                 }
    #                                             }
    #                                         ],
    #                                         size=1
    #                                        )
    #         # resp['hits']['hits'][0]['_source']['created']
    #         pdb.set_trace()
    #         print(f"Got {resp['hits']['total']['value']} Hits.")
    #         # pdb.set_trace()
            
    #     except Exception as e:
    #         raise  Exception(f"Error: {e}")

    #     return resp
    
    def search_ticker(self, 
                index: str, 
                ticker: str,
                conditional: str = 'lte', # or 'gte' or 'eq'
                query_on_key: str = '',
                query_on_val: str = ''
                ):
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
        resp = {}
        if conditional:
            if 'lte' in conditional:
                range_dict = {'lte': query_on_val}
            if 'gte' in conditional:
                range_dict = {'gte': query_on_val}
            if 'eq' in conditional:
                range_dict = {'gte': query_on_val,
                            'lte': query_on_val
                        }
        try:
            if query_on_key:
                assert query_on_val, "Missing value for -query_on_val-"
                query = {'bool': {'must': [
                                {
                                    "term": {'ticker': ticker}
                                },
                                {
                                    "range": {query_on_key: range_dict}
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
    
    def get_latest_news_from_ticker(self, ticker: str):
        
        try:
            resp = self.crud.client.search(index=self.index, 
                                           ignore_unavailable=True,
                                           query={"match": {'ticker': {'query': ticker}}},
                                            sort=[{"created": {"order": "desc"}}],
                                            size=1
                                           )
        except Exception as e:
            raise  Exception(f"Error: {e}")

        if not resp['hits']['total']['value']:
            return None
        
        return resp['hits']['hits'][0]['_source']
    
if __name__ == "__main__":
    nw = newswire()
