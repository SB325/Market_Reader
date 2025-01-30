from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elastic.models import query_model, insert_method, news_article_mapping
from typing import List
import sys, os
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
            max_retries=max_retries,
            basic_auth=("elastic", password)
        )

        if verbose:
            print(client.info())

    def create_schema(self, new_index: str = '', new_settings: dict = {}, new_mapping: dict = {}):
        self.client.indices.create(index=new_index, settings=new_settings, mappings=new_mapping)

    def insert_document(self, method: insert_method = 'index', index: str ='', id: int = None, document: dict = {} ):
        resp = getattr(self.client, method.value)(index=index, id=id, document=document)
        return resp['result']

    def bulk_insert_documents(self, doclist: List[dict] = {}):
        # https://elasticsearch-py.readthedocs.io/en/stable/helpers.html
        def gendata():
            for doc in doclist:
                yield doc

        bulk(self.client, gendata())

    def retrieve_document(self, index: str ='', id: int = None ):
        resp = self.client.get(index=index, id=id)
        return resp['_source']

    def search(self, index: str ='', query: query_model = {}):
        resp = self.client.search(index=index, query={"match_all": {}})
        print("Got %d Hits:" % resp['hits']['total']['value'])
        hits = []
        for hit in resp['hits']['hits']:
            hits.append("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
        return {'NHits': len(hits), 'hits': hits}
    
    def refresh_index(self, index: str = ''):
        self.client.indices.refresh(index=index)
    
    def delete_document(self, index: str ='', id: int = None):
        self.client.delete(index=index, id=id)

    # TODO: configure nodes
    # def adjust_client_options(self, options_dict: dict = {}):
    #     if options_dict:
    #         self.client.options(max_retries=0).index()