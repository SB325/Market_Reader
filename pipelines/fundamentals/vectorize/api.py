# imports
import asyncio 
import os
import sys
sys.path.append('../../../')
sys.path.append('../')
# from util.logger import log
import pdb
from vectorize import add_data_to_vector_db
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn
import json

app: FastAPI = FastAPI()

class FieldStruct(BaseModel):
    cik: str
    reportDate: str
    acceptanceDateTime: str
    uri: str
    primaryDocDescription: str
    filing_content_string: str

class DocStruct(BaseModel):
    id : int
    fields: FieldStruct

# endpoints
@app.get("/add_str_as_vector")
async def root(data: str):
    data_validated = DocStruct(json.loads(data))
    pdb.set_trace()

    if add_data_to_vector_db(data_validated):
        return {"message": "Vector Added"}
    else:
        return {"message": "Failure to add Vector"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)