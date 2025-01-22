import uvicorn
from fastapi import FastAPI #, Body, Request
from fastapi.responses import JSONResponse
from webhook_response_model import webhook_response
import json
import pdb

app: FastAPI = FastAPI(root_path="/bzwebhook")

# endpoints
@app.post("/")
async def root(data: webhook_response):
    response = JSONResponse(status_code=200, content="OK")
    try:
        # do stuff with the data
        data = data.model_dump()
        print(data)
    except:
        # log the error
        return JSONResponse(status_code=204, content="NoContent")
    return response

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8001, reload=True)