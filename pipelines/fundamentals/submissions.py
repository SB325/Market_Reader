from util.logger import log
from util.requests_util import requests_util
from util.crud import crud as crud
from util.db.models.tickers import Company_Meta as cmeta
from util.db.models.tickers import Company_Mailing_Addresses as cmailing
from util.db.models.tickers import Company_Business_Addresses as cbusiness
from util.db.models.filings import Filings as filings
import pandas as pd
import copy
import os
import json
import pdb


requests = requests_util()
crud_util = crud()

current_file = os.path.basename(__file__)

class Submissions():
    # Submissions:
    # List of all listed filing submissions made by the company.
    #  The 'recent' key contains a table of all accessionNumbers (filing identifiers) and the 
    # metadata needed to derive the url (to download the actual pdf).
    url_base = f'https://data.sec.gov/submissions/'
    header = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self):
        # Nearly raw downloaded REST response (dict)
        self.downloaded_data: dict = {}  
        # Top-line company metadata
        self.meta_data: dict = {}
        # Descriptions for all of a company's filings
        self.filings: pd.DataFrame = {}
        self.cik = None
    
    def read_cik(self, cik: str):
        assert cik, "Must pass 10 digit number as an argument!"
        self.cik = '0' * (10-len(cik)) + cik
        self.url = self.url_base + f'CIK{self.cik}.json'

    def download_submission(self, cik: str):
        # download submission from SEC Edgar submissions endpoint for cik.
        self.read_cik(cik)

        try:
            response = requests.get(url_in=self.url, headers_in=self.header)
            response.raise_for_status()
        except BaseException as ex:
            # possibly check response for a message
            log.error(f'{current_file}: HTTPError on url: {self.url}.\n{ex}')
            raise ex  # let the caller handle it
        else:
            self.downloaded_data = response.json()

    def parse_response(self):
        # Set parsing rules and value checks, returning table of interest.
        self.meta_data = copy.deepcopy(self.downloaded_data)
        filings = self.meta_data.pop('filings')
        table = filings['recent']
        self.filings = pd.DataFrame({k:pd.Series(v) for k,v in table.items()})

    def insert_table(self) -> bool:
        # Insert table(s) into database.
        if self.filings.empty:
            log.warning(f"No filings data to insert for cik {self.cik}.")
        else:
            nfilings = len(self.filings.index)
            self.filings = self.filings.assign(cik=[self.cik] * nfilings)
            filings_to_insert = self.filings.to_dict('records')
            
            # Insert company filings
            crud_util.insert_rows(filings, ['accessionNumber'], filings_to_insert)
        
        if not self.meta_data:
            pdb.set_trace()
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            cik_dict = [{'cik': self.cik}] * 2
            metadata = copy.deepcopy(self.meta_data)
            
            metadata['tickers'] = json.dumps(metadata['tickers'])
            metadata['exchanges'] = json.dumps(metadata['exchanges'])
            metadata['formerNames'] = json.dumps(metadata['formerNames'])
            metadata['cik'] = self.cik

            addresses = metadata.pop('addresses')
            cik_dict[0].update(addresses['mailing'])
            cik_dict[1].update(addresses['business'])

            # Insert company metadata
            if metadata['cik']:
                crud_util.insert_rows(cmeta, ['cik'], [metadata])

            # Insert mailing address
            crud_util.insert_rows(cmailing, ['cik'], [cik_dict[0]])

            # Insert business address
            crud_util.insert_rows(cbusiness, ['cik'], [cik_dict[1]])

