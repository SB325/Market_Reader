# from vespa.application import ApplicationPackage
from app_package import app_package
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile, Component, Parameter
from vespa.deployment import VespaDocker
import os
from dotenv import load_dotenv
from vespa.io import VespaResponse
import pdb
import asyncio
from load_model import tokenizer, model
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as langchain_doc
import torch
from tqdm import tqdm
import requests
import os.path

load_dotenv(override=True)

VESPA_CONTAINER_IP = os.getenv("VESPA_CONTAINER_IP")
VESPA_API_PORT = os.getenv("VESPA_API_PORT")
RUNNING_VESPA_API = True

def write_session_id(id: str):
    with open('session_id.txt', 'w') as f:
        f.write(id)

def get_session_id():
    id = ''
    file = 'session_id.txt'
    if os.path.isfile(file):
        with open(file, 'r') as f:
            id = f.read()
    return id

def make_session_object(id: str, endpoint: str):
    obj = {
        'session-id' :  id,
        'content' : f"/application/v2/tenant/default/session/[session-id]/",
        'prepare' : f"/application/v2/tenant/default/session/[session-id]/",
    }   
    obj['content'].replace('[session-id]/',f"{id}/content/")
    obj['prepare'].replace('[session-id]/',f"{id}/prepared/")
    return obj

class DeployVespa():
    session_id : str
    prepared_url : str
    content: str
    session_prepare_url : str
    ip: str
    config_port: str
    upload_endpoint: str = '/application/v2/tenant/default/session'

    def __init__(self, ip: str = VESPA_CONTAINER_IP, port: str = VESPA_API_PORT) -> str:
        self.ip = ip
        self.config_port = port
        url_in = f"http://{ip}:{port}/{self.upload_endpoint}n"
        header = {'Content-Type': 'application/zip'}
        files ={"archive": app_package.to_zip()}
        
        id = get_session_id()
        if id:
            session_obj = make_session_object(id, 
                    "/application/v2/tenant/default/session/[session-id]/"
                    )
            self.session_id = session_obj['session-id']
            self.content = f"http://{self.ip}:{self.config_port}{session_obj['content']}"
            self.session_prepare_url = f"http://{self.ip}:{self.config_port}{session_obj['prepare']}"
        else:
            response = requests.post(
                        url=url_in, 
                        files=files, 
                        headers=header,
                        timeout=5,
                    )
            if not response.ok:
                msg = f"Error {response.status_code}\n{url_in}:\n{response.reason}"
                return msg
            else: 
                msg = response.json()
                session_obj = make_session_object(msg['session-id'], 
                    "/application/v2/tenant/default/session/[session-id]/"
                    )
                self.session_id = session_obj['session-id']
                self.content = f"http://{self.ip}:{self.config_port}{session_obj['content']}"
                self.session_prepare_url = f"http://{self.ip}:{self.config_port}{session_obj['prepare']}"

                write_session_id(self.session_id)

    def prepare_session(self, applicationName: str, 
                        environment: str, 
                        region: str, 
                        instance: str, 
                        debug: bool = True, 
                        timeout: int = 360,
                    ):
        parameters = {'applicationName': applicationName, 
                        'environment': environment, 
                        'region': region, 
                        'instance': instance, 
                        'debug': debug, 
                        'timeout': timeout,
                    }
        pdb.set_trace()
        response = requests.put(
                url=self.session_prepare_url, 
                json=parameters,
            )
        if not response.ok:
            msg = f"Error {response.status_code}:\n{response.reason}"
            pdb.set_trace()
        else: 
            msg = response.json()
            pdb.set_trace()

    def close_session(self, id: str):
        url = f"http://{self.ip}:{self.config_port}/application/v2/tenant/default/session/{id}/content/"
        response = requests.delete(
            url = url
        )
        if not response.ok:
            msg = f"Error {response.status_code}:\n{response.reason}"
            pdb.set_trace()
        else: 
            msg = response.json()
            pdb.set_trace()

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

def add_data_to_vector_db(data: list, use_api: bool = RUNNING_VESPA_API):
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
    
    if use_api:
        # api call to pass documents here. session_id and prepared url should be 
        # in app object
        pass
    else:
        app.feed_iterable(data, 
                schema="doc0", 
                callback=response_callback
                ) 
    return status
    

if __name__ == "__main__":
    if RUNNING_VESPA_API:
        app = DeployVespa(ip = VESPA_CONTAINER_IP, port = VESPA_API_PORT)
        app.prepare_session(applicationName = 'vector0',
                            environment = 'default', 
                            region = 'default', 
                            instance = 'default',
                            )
    pdb.set_trace()
