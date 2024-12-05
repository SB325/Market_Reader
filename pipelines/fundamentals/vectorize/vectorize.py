# from vespa.application import ApplicationPackage
from app_package import app_package
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile, Component, Parameter
from vespa.deployment import VespaDocker
import os
# from dotenv import load_dotenv
from vespa.io import VespaResponse
import pdb
import docker
import asyncio
from load_model import tokenizer, model
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as langchain_doc
import torch
from tqdm import tqdm
import requests

# load_dotenv()   

# model_checkpoint = "google-bert/bert-base-uncased"
# onnx_model_directory = "models"
# CONTAINER_MODEL_DIR = '/opt/vespa/var/models'

# VESPA_LOG_STORAGE = os.getenv('VESPA_LOG_STORAGE')
VESPA_CONTAINER_IP = 'vespa_container'
VESPA_API_PORT = '8080'

cli = docker.DockerClient()
vespa_container_obj = [container for container in cli.containers.list() if container.name=='vespa_container']
vespa_container_obj = vespa_container_obj[0]

# '''
# port – Container port. Default is 8080.
# cfgsrv_port – Vespa Config Server port. Default is 19071.
# debug_port – Port to connect to, to debug the vespa container. Default is 5005.
# output_file – Output file to write output messages.
# container_memory – Docker container memory available to the application in bytes. Default is 4GB.
# container – Used when instantiating VespaDocker from a running container.
# volumes – A list of strings which each one of its elements specifies a mount volume. 
#     For example: [‘/home/user1/:/mnt/vol2’,’/var/www:/mnt/vol1’]. NB! The Application Package can NOT refer to Volume Mount paths. See note above.
# container_image – Docker container image.
# '''
vespa_docker = VespaDocker(port=8080,
                           cfgsrv_port=19071,
                           debug_port=5005,
                           container=vespa_container_obj,
                           )

app = vespa_docker.deploy(application_package=app_package)

def response_callback(response: VespaResponse, id: str):
    if not response.is_successful():
        print(f"Response for id {id} not successful")
    else:
        print(f"Response for id {id} successful")

text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=768,  # chars, not llm tokens
                chunk_overlap=0,
                length_function=len,
                is_separator_regex=False,
                )

def chunk(str_to_chunk: str):
    # chunks = text_splitter.transform_documents([str_to_chunk])
    chunks = text_splitter.split_documents([str_to_chunk])
    return chunks

def add_data_to_vector_db(data: list):
    status = False
    resp = ''
    for dat in data:
    #for dat in tqdm(data, desc='embedding...'):
        str_to_embed = dat['fields']['filing_content_string']
        if str_to_embed:
            doc_to_embed = langchain_doc(
                                    page_content=str_to_embed, 
                                    metadata={"source": f"{dat['fields']['uri']}"}
                                    )
            
            chunked_str_to_embed = chunk(doc_to_embed)
            chunked_list = [sentence.page_content for sentence in chunked_str_to_embed]
            
            with torch.no_grad():
                model_output = model.encode(chunked_list)
            dat['fields'].update( {  
                'embedding': {cnt: val for cnt,val in enumerate(model_output.tolist())}
                } )
            status = True
        else:
            pdb.set_trace()
            print('this shouldnt happen')
    
    app.feed_iterable(data, 
                schema="doc0", 
                callback=response_callback
                ) 
    return status
    
