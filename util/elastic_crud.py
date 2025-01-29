from elasticsearch import Elasticsearch
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

    def adjust_client_options(self, options_dict: dict = {}):
        if options_dict:
            self.client.options(max_retries=0).index()