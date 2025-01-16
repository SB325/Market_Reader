## PolicyRAG LLM application ##
#
# Components:
# 1. Vector store pipelines
# Document parsing, chunking, embedding and loading into vector DB
# 2. Semantic Search
# Introduce relevant documents to LLM prompts via semantic search of vector database given embedded prompts
# 3. LLM framework
# Use OpenAI to generate responses
#####################################################################################################################

## Imports
import os
import sys
import pdb
import glob
import json
from dotenv import load_dotenv
import pandas as pd
import re
import pprint

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain

from vector_query import vector_query

## Env Variables
load_dotenv(override=True)
LLM_MODEL = os.environ.get("LLM_MODEL")

## LLM Framework
llm = OllamaLLM(model=LLM_MODEL)
# main_query = "How many shares of common stock did Senior Vice President, Powertrain and Energy Engineering arrange to sell, and when was the arrangement's expiration date?"
main_query = "After the sale of shares of Common Stock subject to the Underwriters’ option, closed on February 19, 2020, what were the net proceeds?"
# "On November 13, 2023, Andrew Baglino, Senior Vice President, Powertrain and Energy Engineering, 
# adopted a Rule 10b5-1 trading arrangement for the potential sale of up to 115,500 shares of our 
# common stock, subject to certain conditions. The arrangement's expiration date is December 31, 2024"

# response0 = llm.invoke(main_prompt)
# print(response0)
# pdb.set_trace()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional macro economics article writer."),
        ("user", "{input}")
])
# system - chatbot system config
# user - user input
# human - user?
# ai - model

# chain = prompt | llm 

# output_parser = StrOutputParser()

# chain = prompt | llm | output_parser

# response2 = chain.invoke({"input": main_query})
# print(response2)  

############### Retrieval Chain
prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")

document_chain = create_stuff_documents_chain(llm, prompt)
vquery = vector_query()
context = vquery.query_semantic(main_query)
documents = vquery.get_returned_documents(context)

docs = [Document(page_content=doc) for doc in documents]

response3 = document_chain.invoke({
        "input": main_query,
            "context": docs
            })

print(response3) 
pdb.set_trace()

#################### Conversation Retrieval Chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
                ("user", "Given the above conversation, generate a search query to look up to get information relevant to the conversation")
                ])
# pdb.set_trace()
retriever_chain = create_history_aware_retriever(llm, retriever, prompt)

from langchain_core.messages import HumanMessage, AIMessage

chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
retriever_chain.invoke({
        "chat_history": chat_history,
            "input": "Tell me how"
            })

prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the user's questions based on the below context:\n\n{context}"),
            MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                ])
# pdb.set_trace()
document_chain = create_stuff_documents_chain(llm, prompt)
# pdb.set_trace()
retrieval_chain = create_retrieval_chain(retriever_chain, document_chain)

chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
response = retrieval_chain.invoke({
        "chat_history": chat_history,
            "input": "Tell me how"
            })
print(response)
