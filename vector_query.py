from app_package import app_package
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile, Component, Parameter
from vespa.deployment import VespaDocker
from vespa.io import VespaQueryResponse
from pipelines.fundamentals.vectorize import tokenizer, app
import os
from dotenv import load_dotenv
import pdb
import docker
# import asyncio
import torch
from tqdm import tqdm

load_dotenv()   
VESPA_CONTAINER_IP = '172.22.0.5'
VESPA_CONFIG_PORT = '4000'

#cli = docker.DockerClient()
#vespa_container_obj = [container for container in cli.containers.list() if container.name=='vespa_container']
#vespa_container_obj = vespa_container_obj[0]

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
#vespa_docker = VespaDocker(port=8080,
#                           cfgsrv_port=19071,
#                           debug_port=5005,
#                           container=vespa_container_obj,
#                           )

#app = vespa_docker.deploy(application_package=app_package)

embedded_str = tokenizer("*", 
                          padding=True, 
                          truncation=True, 
                          return_tensors='pt'
                          )

with app.syncio() as session:
    response: VespaQueryResponse = session.query(
                yql="select * from sources * where userQuery()",
                hits=1,
                query=embedded_str,
                ranking="tensor-default",
            )

    if response.is_successful():
        response_url = response.url
        ndocuments = response.number_documents_retrieved
        operation = response.operation_type
        nretrieved = response.number_documents_indexed
        response_body = response.json
        hits = response.hits
        print(
            f"NDocuments: {ndocuments}\n" + \
            f"Operation: {operation}\n" + \
            f"NRetrieved: {nretrieved}\n" + \
            f"Hits: {hits}\n" +  \
            f"Response Body: {response_body}\n" + \
            f"Response URL: {response_url}\n" 
        )
    else:
        print("Response Error")
        pdb.set_trace()
    
