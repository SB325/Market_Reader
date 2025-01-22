from elasticsearch import Elasticsearch
import sys, os
import pdb
from dotenv import load_dotenv

# sys.path.append("../../../../")
load_dotenv(override=True, dotenv_path='../../creds.env')  
load_dotenv(override=True, dotenv_path='../../../../.env')
pw = os.getenv("ELASTIC_PASSWORD")
cert_loc = os.getenv("ELASTIC_CERT_LOC")
print(cert_loc)
NODES = [
    "https://172.22.0.5:9200"
]

client = Elasticsearch(
    NODES,
    ca_certs=f"{cert_loc}/ca.crt",
    basic_auth=("elastic", pw)
)

client.info()