from langchain_ollama import OllamaEmbeddings

# add elastic
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.documents import Document
from uuid import uuid4

import os
from dotenv import load_dotenv

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

ELASTIC_IP = os.getenv("ELASTIC_IP")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")
ELASTIC_PW = os.getenv("ELASTIC_PASSWORD")

embeddings = OllamaEmbeddings(model="llama3.1:8b")

def get_splitter():
    return RecursiveCharacterTextSplitter(
                chunk_size=768,  # chars, not llm tokens
                chunk_overlap=0,
                length_function=len,
                is_separator_regex=False,
                )

def chunk(str_to_chunk: str):
    chunks = get_splitter().split_documents([str_to_chunk])
    return chunks

class ElasticClass():
    ip: str
    port: str

    def __init__(self, ip: str = ELASTIC_IP, port: str = ELASTIC_PORT, verbose: bool = False):
        self.ip = ip
        self.port = port
        self.es = ElasticsearchStore(
            es_url=f"http://{ip}:9200",
            index_name="langchain_index",
            embedding=embeddings,
            es_user="elastic",
            es_password=ELASTIC_PW,
            # if you use the model_id
            # strategy=DenseVectorStrategy(model_id="test_model")
            # if you use hybrid search
            # strategy=DenseVectorStrategy(hybrid=True)
        )

        if verbose:
            self.es.info().body

    def add_documents(self, document_obj: list, index: str):
        doclist = []
        for doc in document_obj:
            doclist.append(
                    Document(
                        page_content=doc['content'],
                        metadata={"source": doc['source']},
                    )
            )
        
        uuids = [str(uuid4()) for _ in range(len(doclist))]

        self.es.add_documents(documents=doclist, ids=uuids)

    def delete_from_vectorstore(self, uuid_list: list):
        self.es.delete(ids=uuid_list)

    def query(self, field: str, query_str: str):
        results = self.es.similarity_search(
            query=query_str,
            k=2,
            filter=[{"term": {"metadata.source.keyword": field}}],
        )
        for res in results:
            print(f"* {res.page_content} [{res.metadata}]")
    
    def query_score(self, field: str, query_str: str):
        results = self.es.similarity_search_with_score(
            query="Will it be hot tomorrow",
            k=1,
            filter=[{"term": {"metadata.source.keyword": "news"}}],
        )
        for doc, score in results:
            print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")

    def retriever(self, prompt: str, threshold: float = 0.2):
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold", search_kwargs={"score_threshold": threshold}
        )
        retriever.invoke(prompt)

    def __del__(self, id: str):
        self.es.transport.close()



def add_data_to_vector_db(data: list):
    status = False
    resp = ''
    for dat in data:
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
        # app.feed_iterable(data, 
        #         schema="doc0", 
        #         callback=response_callback
        #         ) 
    return status
    

if __name__ == "__main__":

    pdb.set_trace()
