# Benzinga News API client
import pdb
import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__)))
from util.requests_util import requests_util
from util.elastic.crud_elastic import crud_elastic
from util.elastic.models import (
    news_article_model, 
    news_article_mapping,
    text_embeddings_mapping
)
from util.time_utils import posix_to_datestr, to_posix
from newswire_params import NewsAPIParams
from typing import List
from elasticsearch.helpers import bulk
from pprint import pprint

load_dotenv(override=True, dotenv_path='newsapi_creds.env')  
load_dotenv()
model_name = os.getenv("EMBEDDING_MODEL_NAME")
key = os.getenv("BENZINGA_API_KEY")

url = "https://api.benzinga.com/api/v2/news"
headers = {"accept": "application/json"}

requests = requests_util()

class newswire():
    embedding_model = ""
    def __init__(self, crud: crud_elastic, embedding_model: str ="", key: str = key):
        self.key = key
        self.index = 'market_news'
        self.embedding_model = embedding_model
        self.crud = crud
        # check if index exists, create if it doesn't

        if not self.crud.client.indices.exists(index=self.index):
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
    
    def check_pipelines(self, pipeline_name: str):
        try:
            val = self.crud.client.ingest.get_pipeline(id = pipeline_name,
                                                    error_trace=False)
        except:
            return None
        return val
    
    def delete_pipeline(self, pipeline_name: str='news_embed_pipeline'):
        try:
            val = self.crud.client.ingest.delete_pipeline(id = pipeline_name)
        except:
            print(f"Failed to delete pipeline -{pipeline_name}-")
            return None
        return val
    
    def create_pipeline(self, pipeline_name: str='news_embed_pipeline'):
        if not self.check_pipelines(pipeline_name=pipeline_name):
            resp = self.crud.create_ingest_pipeline(pipeline_name=pipeline_name,
                                         target_fields= ['title','body'],
                                         model=self.embedding_model,
                                         verbose=True)
        # model is just a string. where does elastic get the actual model?
            
    def embed_text(self):
        resp = self.crud.reindex_text_to_embedding_mappings(source_index='news_article_mapping',
                                                     destination_index='text_embeddings_mapping',
                                                     pipeline_name='news_embed_pipeline',
                                                     verbose=True)

    def search(self, 
               embeddings_field: str,
               search_string: str,
               returned_fields: List[str],
               k: int = 10,
               num_candidates: int = 100):
        self.crud.vector_search(index='market_news',
                                embeddings_field=embeddings_field,
                                embedding_model=self.embedding_model,
                                search_string=search_string,
                                k=k,
                                num_candidates=num_candidates,
                                returned_fields=returned_fields,
                                verbose=True)

    def search_ticker(self, 
                index: str, 
                ticker: str,
                conditional: str = 'lte', # or 'gte' or 'eq'
                query_on_key: str = '',
                query_on_val: str = '',
                verbose: bool = False
                ):
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
        resp = {}
        if conditional:
            if 'lte' in conditional:
                range_dict = {'lte': query_on_val}
            if 'gte' in conditional:
                range_dict = {'gte': query_on_val}
            if 'eq' in conditional:
                if len(query_on_val)==1:
                    range_dict = {'gte': query_on_val,
                            'lte': query_on_val
                        }
                elif len(query_on_val)==2:
                    range_dict = {'gte': query_on_val[0],
                            'lte': query_on_val[1]
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
            if verbose:
                print(f"Got {resp['hits']['total']['value']} Hits for ticker {ticker}.")
            
        except Exception as e:
            raise  Exception(f"Error: {e}")

        return resp
    
    def get_latest_news_from_ticker(self, ticker: str):
        
        try:
            resp = self.crud.client.search(index=self.index, 
                                            ignore_unavailable=True,
                                            query={"match": {"ticker": {"query": ticker}}},
                                            sort=[{"created": {"order": "desc"}}],
                                            size=1  
                                           )
        except Exception as e:
            raise  Exception(f"Error: {e}")

        if not resp['hits']['total']['value']:
            return None
        
        return resp['hits']['hits'][0]['_source']
    
if __name__ == "__main__":
    nw = newswire(crud=crud_elastic(), 
                  embedding_model=model_name)
    
    desired_first_time = to_posix(
                    "03/27/2025 02:00 AM", dateformat_str = "%m/%d/%Y %I:%M %p"
                    )*1000
    desired_last_time = to_posix(
                    "03/27/2025 09:00 PM", dateformat_str = "%m/%d/%Y %I:%M %p"
                    )*1000
    response = nw.search_ticker(index=nw.index, 
                                        ticker='CNTM',
                                        # conditional='eq',
                                        # query_on_key = 'created',
                                        # query_on_val = [desired_first_time,desired_last_time]
                                        )
    # # nw.create_pipeline()
    # # nw.delete_pipeline()
    # pdb.set_trace()