from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class msg_str_operator(Enum):
    _and = "and"
    _or = "or"

class msg_fuzziness(Enum):
    # The maximum allowed Levenshtein Edit Distance
    _0 = '0'
    _1 = '1'
    _2 = '2'
    _3 = '3'
    _4 = '4'
    _5 = '5'
    AUTO = 'AUTO'

class msg_zero_terms_query(Enum):
    none = 'none'
    all = 'all'

class msg_struct(BaseModel):
    query: str
    operator: Optional[msg_str_operator]
    fuzziness: Optional[msg_fuzziness]
    zero_terms_query: Optional[msg_zero_terms_query]
    auto_generate_synonyms_phrase_query: Optional[bool]


class message(BaseModel):
    message: msg_str_operator |  msg_struct

class sqs(BaseModel):
    query: str = ""
    fields: Optional[list] = []
    default_operator: Optional[str] = ""

class query_model(BaseModel):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
    match: Optional[message]
    match_all: Optional[dict]
    match_none: Optional[dict]
    term: Optional[dict]  # exact match of field. {'term': {'ticker': 'AAPL'}}
    simple_query_string: Optional[sqs]

class insert_method(Enum):
    index = 'index'
    update = 'update'

class news_article_model(BaseModel):
    _id: int
    ticker: str
    author: str
    created: str
    updated: str
    title: str
    teaser: str
    body: str
    channels: str

# first index
news_article_mapping =  {
    "properties": {
        "id":    { "type" : "keyword"},
        "ticker": { "type" : "keyword" }, 
        "author":  { "type" : "text"}, 
        "created":  { "type" : "date" },
        "updated":  { "type" : "date" },
        "title":  { "type" : "text" }, 
        "teaser":  { "type" : "text" }, 
        "body":  { "type" : "text" }, 
        "channels":  { "type" : "text" },    
    },
    "dynamic_date_formats" : [
        "EEE, dd LLL yyyy HH:mm:ss ZZZZZ||epoch_second"  
    ]
}
# second index
text_embeddings_mapping = {
        "properties": {
            "body.embedded_value": {
                "type": "dense_vector"
            },
            "body": {
                "type": "text"
            },
            "title.embedded_value": {
                "type": "dense_vector"
            },
            "title": {
                "type": "text"
            }
        }
    }



