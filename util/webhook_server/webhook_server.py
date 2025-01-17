import uvicorn
from fastapi import FastAPI, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import json

import pdb

app: FastAPI = FastAPI(root_path="/test")

class content(BaseModel):
    hi : str

# endpoints
@app.post("/test_endpoint")
async def root(data: Request):
    # async def root(data: str = Body(..., embed=True)):
    # pdb.set_trace()   
    # try:
    # payload = data #.model_dump_json()
    # except:
    #     return JSONResponse({"message": "Custom JSON Response"}, status_code=201)
    # datadict = await data.json()
    # print(json.dumps(datadict))
    print(await data.json())
    # return JSONResponse(status_code=200, content="ok")

if __name__ == "__main__":
    uvicorn.run("fake_server:app", host="0.0.0.0", port=8001, reload=True)