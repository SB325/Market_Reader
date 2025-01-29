from pydantic import BaseModel #, ValidationError
from enum import Enum, IntEnum
from typing import List
import pdb

class NewswireResponse(BaseModel):
   id: str = " "                         # Newswire id
   author: str = " "                     # Author of newswire
   created: str = " "                   # datestring
   updated: str = " "                   # datestring
   title: str = " "                     # Title of newswire 
   teaser: str = " "                       # teaser 
   body: str = " "                         # likely HTML format
   url: str = " "                          # 
   image: List[dict]
   channels: List[dict]                        # Topic
   stocks: List[dict]                       # Named tickers
   tags: List[dict]                      # Named Tags?


