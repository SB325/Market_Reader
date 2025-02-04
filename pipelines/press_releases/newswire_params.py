from pydantic import BaseModel, ValidationError
from enum import Enum, IntEnum
from typing import List
import pdb

class displayOutputEnum(str, Enum):
   # Specify headline only (headline), headline + teaser (abstract), or headline + full body (full) text
   full = 'full'
   abstract = 'abstract'
   headline = 'headline'

class sortResponse(str, Enum):
   # Allows control of results sorting. [Default=DESC].
   id_asc = 'id:asc'
   id_desc = 'id:desc'
   created_asc = 'created:asc'
   created_desc = 'created:desc'
   updated_asc = 'updated:asc'
   updated_desc = 'updated:desc'

class NewsAPIParams(BaseModel):
   page: int = None                         # Page offset.
   pageSize: int = None                     # Number of results returned.
   displayOutput: displayOutputEnum = 'headline'
   date: str = None                         # The date to query for news. Shorthand for date_from and date_to if they are the same.
   dateFrom: str = None                     # Date to query from point in time. Sorted by published date.
   dateTo: str = None                       # Date to query to point in time. Sorted by published date.
   updatedSince: int = None                 # The last updated Unix timestamp (UTC) to pull and sort by
   publishedSince: int = None               # The last published Unix timestamp (UTC) to pull and sort by
   sort: sortResponse = None 
   isin: str = None                         # One or more ISINs separated by a comma. Maximum 50
   cusip: str = None                        # One or more CUSIPs separated by a comma. Maximum 50. License agreement required.
   tickers: str = None                      # One or more ticker symbols separated by a comma. Maximum 50.
   channels: str = None                     # One or more channel names or IDs separated by a comma
   topics: str = None                       # One or more words/phrases separated by a comma; searches Title, Tags, and Body in order of priority.
   authors: str = None                      # One or more authors separated by a comma
   content_types: str = None                # One or more content types separated by a comma


