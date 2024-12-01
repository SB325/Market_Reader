## PolicyRAG LLM application ##
# This application collects Federal statutes and legislation documents and indexes them to support Public policy LLMs.
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

# Once you've installed and initialized the LLM of your choice, we can try using it! 
# Let's ask it what LangSmith is - this is something that wasn't present in 
# the training data so it shouldn't have a very good response.
# print('Prompt Exercise 1:')
# response0 = llm.invoke(main_prompt)
# print(response0)
# pdb.set_trace()

# We can also guide its response with a prompt template. 
# Prompt templates convert raw user input to better input to the LLM.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional macro economics article writer."),
        ("user", "{input}")
])
# system-think of as a chatbot system config
# user - user input
# human - user?
# ai - model

# We can now combine these into a simple LLM chain:
# chain = prompt | llm 

# # We can now invoke it and ask the same question. It still won't know the answer, 
# # but it should respond in a more proper tone for a technical writer!
# print('Prompt Exercise 2:')
# response1 = chain.invoke({"input": main_query})
# print(response1) # Sounds good, but the details are fabricated.
# pdb.set_trace()

# The output of a ChatModel (and therefore, of this chain) is a message. 
# However, it's often much more convenient to work with strings. 
# Let's add a simple output parser to convert the chat message to a string.

# output_parser = StrOutputParser()

# # # We can now add this to the previous chain:
# chain = prompt | llm | output_parser

# # We can now invoke it and ask the same question. 
# # The answer will now be a string (rather than a ChatMessage).
# print('Prompt Exercise 3:')
# response2 = chain.invoke({"input": main_query})
# print(response2)  # Similar as PE2.

############### Retrieval Chain
# To properly answer the original question ("how can langsmith help with testing?"), 
# we need to provide additional context to the LLM. We can do this via retrieval. 
# Retrieval is useful when you have too much data to pass to the LLM directly. 
# You can then use a retriever to fetch only the most relevant pieces and pass those in.

# In this process, we will look up relevant documents from a Retriever and then 
# pass them into the prompt. A Retriever can be backed by anything - a SQL table, 
# the internet, etc - but in this instance we will populate a vector store and use that as a retriever. 
# For more information on vectorstores, see this documentation.
############

# First, let's set up the chain that takes a question and the retrieved documents and generates an answer.
prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")

document_chain = create_stuff_documents_chain(llm, prompt)
vquery = vector_query()
context = vquery.query_semantic(main_query)
documents = vquery.get_returned_documents(context)

print('Prompt Exercise 4:')
docs = [Document(page_content=doc) for doc in documents]

response3 = document_chain.invoke({
        "input": main_query,
            "context": docs
            })

print(response3) 
pdb.set_trace()

#################### Conversation Retrieval Chain
# The chain we've created so far can only answer single questions. 
# One of the main types of LLM applications that people are building are chat bots. 
# So how do we turn this chain into one that can answer follow up questions?

# We can still use the create_retrieval_chain function, but we need to change two things:

# The retrieval method should now not just work on the most recent input, 
# but rather should take the whole history into account.
# The final LLM chain should likewise take the whole history into account
# Updating Retrieval

# In order to update retrieval, we will create a new chain. This chain will take in 
# the most recent input (input) and the conversation history (chat_history) and use an LLM to generate a search query.

# from langchain.chains import create_history_aware_retriever
# from langchain_core.prompts import MessagesPlaceholder

# # First we need a prompt that we can pass into an LLM to generate this search query

# prompt = ChatPromptTemplate.from_messages([
#         MessagesPlaceholder(variable_name="chat_history"),
#             ("user", "{input}"),
#                 ("user", "Given the above conversation, generate a search query to look up to get information relevant to the conversation")
#                 ])
# # pdb.set_trace()
# retriever_chain = create_history_aware_retriever(llm, retriever, prompt)

# # We can test this out by passing in an instance where the user asks a follow-up question.
# from langchain_core.messages import HumanMessage, AIMessage

# chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
# retriever_chain.invoke({
#         "chat_history": chat_history,
#             "input": "Tell me how"
#             })

# # You should see that this returns documents about testing in LangSmith. 
# # This is because the LLM generated a new query, combining the chat history with the follow-up question.

# # Now that we have this new retriever, we can create a new chain to continue the 
# # conversation with these retrieved documents in mind.
# prompt = ChatPromptTemplate.from_messages([
#         ("system", "Answer the user's questions based on the below context:\n\n{context}"),
#             MessagesPlaceholder(variable_name="chat_history"),
#                 ("user", "{input}"),
#                 ])
# # pdb.set_trace()
# document_chain = create_stuff_documents_chain(llm, prompt)
# # pdb.set_trace()
# retrieval_chain = create_retrieval_chain(retriever_chain, document_chain)

# # We can now test this out end-to-end:
# chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
# response = retrieval_chain.invoke({
#         "chat_history": chat_history,
#             "input": "Tell me how"
#             })
# print(response)
# # We can see that this gives a coherent answer - we've successfully turned our retrieval chain into a chatbot!
