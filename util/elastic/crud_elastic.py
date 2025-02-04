from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys, os
sys.path.append("../../")
from .models import query_model, insert_method
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

    def create_index(self, 
                        new_index: str = '',
                        new_mapping: dict = {}
                        ):
        resp = {}
        try:
            resp = self.client.indices.create(index=new_index, mappings=new_mapping)
        except Exception as e:
            print(f"Error: {e}")
        return resp

    def get_index(self, index: str):
        return self.client.indices.exists(index=index)

    def get_mappings(self):
        all_indices = {}
        try:
            all_indices = self.client.indices.get_mapping()
        except Exception as e:
            print(f"Error: {e}")
        return all_indices.raw
        
    def insert_document(self, 
                        method: insert_method = 'index', 
                        index: str = '', 
                        document: dict = {},
                        ):
        resp = []
        try:
            resp = getattr(self.client, method)(index=index, id=id, document=document)
        except Exception as e:
            print(f"Error: {e}")
        return resp['result']

    # https://elasticsearch-py.readthedocs.io/en/stable/helpers.html
    def bulk_insert_documents(self,
                        index: str,
                        body: List[dict] = {},
                        ):
        
        resp = {}
        try:
            def gendata():
                for doc in body:
                   yield {
                       "_index" : index,
                       "source": doc
                   }
            
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

    def search_ticker(self, 
                index: str, 
                ticker: str,
                ):
        resp = {}
        
        try:
            query = {"query_string" : {
                "query": ticker,
                }
            }
            resp = self.client.search(index=index, query=query)
            print(f"Got {len(resp['hits']['hits'])} Hits.")
            
            
        except Exception as e:
            print(f"Error: {e}")

        return resp
    
    def refresh_index(self, 
                      index: str = '',
                      ):
        try:
            resp = self.client.indices.refresh(index=index)
        except Exception as e:
            print(f"Error: {e}")
        
        return resp
    
    def count_documents(self, 
                        index: str ='*', 
                        id: int = None,
                        ):
        ndocs = self.client.count(index=index)
        return ndocs
    
    def delete_index(self,
                     index: str,
                     ):
        self.client.indices.delete(index=index)

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