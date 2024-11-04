from vespa.application import ApplicationPackage
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile, Component, Parameter
from vespa.deployment import VespaDocker
import os
from dotenv import load_dotenv
import pdb
import docker
import asyncio
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as langchain_doc
import torch
from tqdm import tqdm

# from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer, AutoModel, pipeline

load_dotenv()   
# https://github.com/huggingface/tokenizers/tree/main/bindings/python 

# model_path = '../../../../tokenizers/bindings/python/models/'
model_checkpoint = "google-bert/bert-base-uncased"
onnx_model_directory = "models"
CONTAINER_MODEL_DIR = '/opt/vespa/var/models'
VESPA_MODEL_STORAGE = os.getenv("VESPA_VAR_STORAGE") + '/models'
VESPA_LOG_STORAGE = os.getenv('VESPA_LOG_STORAGE')
VESPA_CONTAINER_IP = '172.22.0.1'
VESPA_CONFIG_PORT = '19071'

if not os.path.exists(f'{VESPA_MODEL_STORAGE}/model.safetensors'):
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    # Load a model from transformers and export it to ONNX
    # ort_model = ORTModelForSequenceClassification.from_pretrained(model_checkpoint, export=True)
    # tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    # Save the onnx model and tokenizer
    # ort_model.save_pretrained(VESPA_MODEL_STORAGE)
    # tokenizer.save_pretrained(VESPA_MODEL_STORAGE)
    model.save_pretrained(VESPA_MODEL_STORAGE)
    tokenizer = AutoTokenizer.from_pretrained(VESPA_MODEL_STORAGE)
else:
    # ort_model = ORTModelForSequenceClassification.from_pretrained(VESPA_MODEL_STORAGE)
    # tokenizer = AutoTokenizer.from_pretrained(VESPA_MODEL_STORAGE)
    model = AutoModel.from_pretrained(VESPA_MODEL_STORAGE)
    tokenizer = AutoTokenizer.from_pretrained(VESPA_MODEL_STORAGE)

cli = docker.DockerClient()
vespa_container_obj = [container for container in cli.containers.list() if container.name=='vespa_container']
vespa_container_obj = vespa_container_obj[0]

# cluster name is the apppackage name with "_content" appended to it.
app_package = ApplicationPackage(
    name="vector0",                              
    schema=[                                    
        Schema(
            name="doc0",
            document=Document(
                fields=[
                    Field(name="id", type="string", indexing=["attribute", "summary"]),
                    Field(
                        name="cik",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="uri",
                        type="uri",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="primaryDocDescription",
                        type="string",
                        indexing=["attribute", "index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="filing_content_string",
                        type="string",
                        indexing=["attribute", "index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="filing_content_embedding",
                        type="tensor<bfloat16>(x[768])",
                        indexing=["attribute", "summary", "index"],
                        ann=HNSW(       # https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW
                            distance_metric="innerproduct",
                            max_links_per_node=16,
                            neighbors_to_explore_at_insert=128,
                        ),
                    ),
                ]
            ),
            fieldsets=[FieldSet(name="default", fields=["primaryDocDescription", "filing_content_string"])],
            rank_profiles=[
                RankProfile(   # https://docs.vespa.ai/en/reference/schema-reference.html#rank-profile
                    name="default",
                    inputs=[("query(q)", "tensor<float>(x[1536])")],
                    first_phase="closeness(field, filing_content_embedding)",
                )
            ],
        )
    ],
    # components=[Component(id="hf-embedder", type="hugging-face-embedder",
    #                     parameters=[
    #                         Parameter("transformer-model", {"path": f"{CONTAINER_MODEL_DIR}/model.onnx"}),
    #                         Parameter("tokenizer-model", {"path": f"{CONTAINER_MODEL_DIR}/tokenizer.json"}),
    #                         ]         
    #                     )
    #             ],
)

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

def response_callback(response, id):
    print(f"Response for id {id}: {response.status_code}")

text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=768,  # chars, not llm tokens
                chunk_overlap=0,
                length_function=len,
                is_separator_regex=False,
                )

def chunk(str_to_chunk: str):
    chunks = text_splitter.transform_documents([str_to_chunk])
    return chunks

def add_data_to_vector_db(data: list):
    data_chunks = []
    for dat in tqdm(data, desc='embedding...'):
        str_to_embed = dat['filing_content_string']
        if str_to_embed:
            doc_to_embed = langchain_doc(page_content=str_to_embed, 
                                    metadata={"source": f"{dat['uri']}"}
                                    )
            
            chunked_str_to_embed = chunk(doc_to_embed)
            chunked_list = [sentence.page_content for sentence in chunked_str_to_embed]
            embedded_list = tokenizer(chunked_list, padding=True, truncation=True, return_tensors='pt')

            with torch.no_grad():
                model_output = model(**embedded_list)

            dat.update( { 'filing_content_embedding': model_output } )
        else:
            pdb.set_trace()
            print('this shouldnt happen')
    # pdb.set_trace()
    # Feed iterable takes list of dicts as -data-
    app.feed_iterable(data, schema="doc", callback=response_callback) 

# '''
# If :class: ContainerCluster is used, any :class: Component`s must be added to the :class: 
# `ContainerCluster, rather than to the :class: ApplicationPackage, 
# in order to be included in the generated schema.
# '''
# ContainerCluster(id="example_container",
#    components=[Component(id="e5", type="hugging-face-embedder",
#        parameters=[
#            Parameter("transformer-model", {"url": "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx"}),
#            Parameter("tokenizer-model", {"url": "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"})
#        ]
#    )],
#    auth_clients=[AuthClient(id="mtls", permissions=["read", "write"])],
#    nodes=Nodes(count="2", parameters=[Parameter("resources", {"vcpu": "4.0", "memory": "16Gb", "disk": "125Gb"})])
# )

# '''
# Define a simple application package:      
# https://docs.vespa.ai/en/reference/schema-reference.html#field
# '''



# '''
# Visiting is a feature to efficiently get or process a set of documents, 
# identified by a document selection expression. Visit yields multiple slices 
# (run concurrently) each yielding responses (depending on number of documents in each slice). 
# This allows for custom handling of each response.
# '''
# all_docs = []
# for slice in app.visit(
#     content_cluster_name="vector_content",
#     schema="doc",
#     namespace="benchmark",
#     selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
#     slices=4,
#     wanted_document_count=300,
# ):
#     for response in slice:
#         print(response.number_documents_retrieved)
#         all_docs.extend(response.documents)

# ''' 
# Delete all the synthetic data with a custom generator. 
# '''
# def my_delete_generator() -> dict:
#     for i in range(1000):
#         yield {"id": str(i)}

#     app.feed_iterable(
#         iter=my_delete_generator(),
#         schema="doc",
#         namespace="benchmark",
#         callback=callback,
#         operation_type="delete",
#         max_queue_size=5000,
#         max_workers=48,
#         max_connections=48,
#     )

# '''
# Updates
# We can also perform other update operations, see Vespa docs on reads and writes. 
# To achieve this we need to set the auto_assign parameter to False in the feed_iterable 
# method (which will pass this to update_data_point-method).
# '''
# def my_update_generator() -> dict:
#     for i in range(1000):
#         yield {"id": str(i), "fields": {"popularity": 2.0}}
# app.feed_iterable(
#     iter=my_update_generator(),
#     schema="doc",
#     namespace="benchmark",
#     callback=callback,
#     operation_type="update",
#     max_queue_size=4000,
#     max_workers=12,
#     max_connections=12,
# )

# from vespa.io import VespaQueryResponse

# with app.syncio(connections=1):
#     response: VespaQueryResponse = app.query(
#         yql="select id from doc where popularity > 2.5", hits=0
#     )
#     print(response.number_documents_retrieved)

# # Feeding operations from a file
# # This demonstrates how we can use feed_iter to feed from a large file without reading the entire file, this also uses a generator.

# # Dump some operation to a jsonl file, we store it in the format expected by pyvespa
# # This to demonstrate feeding from a file in the next section.
# import json

# with open("documents.jsonl", "w") as f:
#     for doc in dataset:
#         d = {"id": doc["_id"], "fields": {"id": doc["_id"], "embedding": doc["openai"]}}
#         f.write(json.dumps(d) + "\n")

# #Get and Feed individual data points
# #Feed a single data point to Vespa

# with app.syncio(connections=1):
#     response: VespaResponse = app.feed_data_point(
#         schema="doc",
#         namespace="benchmark",
#         data_id="1",
#         fields={
#             "id": "1",
#             "title": "title",
#             "body": "this is body",
#             "popularity": 1.0,
#         },
#     )
#     print(response.is_successful())
#     print(response.get_json())

# Cleanup
# vespa_docker.container.stop()
# vespa_docker.container.remove()
