from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys, os
sys.path.append("../../")
from .models import query_model, insert_method, news_article_model, news_article_mapping
from typing import List

import pdb
from dotenv import load_dotenv

load_dotenv(override=True, dotenv_path='../../creds.env')  
load_dotenv(override=True, dotenv_path='../../../../.env')
pw = os.getenv("ELASTIC_PASSWORD")
cert_loc = os.getenv("ELASTIC_CERT_LOC")
cert = "/home/sheldon/src/homeserver/elastic/certs/ca/ca.crt"

class crud_elastic():
    def __init__(self, 
                node_url = "https://127.0.0.1:9200", 
                certfile = cert,
                password = pw,
                max_retries=5,
                verbose = False,
                ):

        self.client = Elasticsearch(
            node_url,
            ca_certs=certfile,
            # verify_certs=False,
            max_retries=max_retries,
            basic_auth=("elastic", password)
        )

        if verbose:
            print(self.client.info())

    def create_schema(self, 
                        new_mapping: dict = news_article_mapping,
                        new_index: str = '', 
                        new_settings: dict = {}, 
                        ):
        resp = {}
        try:
            resp = self.client.indices.create(index=new_index, settings=new_settings, mappings=new_mapping)
        except Exception as e:
            print(f"Error: {e}")
        return resp

    def get_schemas(self):
        all_indices = {}
        try:
            all_indices = self.client.indices.get_alias()
            pdb.set_trace()
        except Exception as e:
            print(f"Error: {e}")
        return all_indices
        
    def insert_document(self, 
                        method: insert_method = 'index', 
                        index: str = '', 
                        document: news_article_model = {},
                        ):
        try:
            resp = getattr(self.client, method.value)(index=index, id=id, document=document.model_dump())
        except Exception as e:
            print(f"Error: {e}")
        return resp['result']

    def bulk_insert_documents(self, 
                        doclist: List[news_article_model] = {},
                        ):
        # https://elasticsearch-py.readthedocs.io/en/stable/helpers.html
        resp = {}
        try:
            def gendata():
                for doc in doclist:
                    yield doc

            resp = bulk(self.client, gendata())
        except Exception as e:
            print(f"Error: {e}")
        return resp
    
    def retrieve_document(self, 
                          index: str ='', 
                          id: int = None,
                          ):
        try:
            resp = self.client.get(index=index, id=id)
        except Exception as e:
            print(f"Error: {e}")
            
        return resp['_source']

    def search(self, 
                index: str ='', 
                query: query_model = {},
                ):
        try:
            resp = self.client.search(index=index, query={"match_all": {}})
            print("Got %d Hits:" % resp['hits']['total']['value'])
            hits = []
            for hit in resp['hits']['hits']:
                hits.append("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
        except Exception as e:
            print(f"Error: {e}")

        return {'NHits': len(hits), 'hits': hits}
    
    def refresh_index(self, 
                      index: str = '',
                      ):
        try:
            resp = self.client.indices.refresh(index=index)
        except Exception as e:
            print(f"Error: {e}")
        
        return resp
    
    def delete_document(self, 
                        index: str ='', 
                        id: int = None,
                        ):
        try:
            resp = self.client.delete(index=index, id=id)
        except Exception as e:
            print(f"Error: {e}")

        return resp
    
    # TODO: configure nodes
    # def adjust_client_options(self, options_dict: dict = {}):
    #     if options_dict:
    #         self.client.options(max_retries=0).index()

if __name__ == "__main__":
    crud = crud_elastic()
    pdb.set_trace()