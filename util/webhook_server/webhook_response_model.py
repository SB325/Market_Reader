from pydantic import BaseModel
from typing import List

class content_body(BaseModel):
    id: int
    revision_id: int
    type: str
    created_at: str
    updated_at: str
    title: str
    body: str
    authors: List[str]
    teaser: str
    url: str
    tags: List[str]
    securities: List[dict]
    channels: List[str]

class webhook_data(BaseModel):
    action: str
    id: int
    content: content_body
    timestamp: str

class webhook_response(BaseModel):
    id: str
    api_version: str
    kind: str
    data: webhook_data