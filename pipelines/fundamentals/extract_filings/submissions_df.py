import asyncio
from util.logger import log
from util.requests_util import requests_util
from util.postgres.db.models.tickers import Symbols as symbols
from util.postgres.db.models.tickers import Company_Meta as cmeta
from util.postgres.db.models.tickers import Company_Mailing_Addresses as cmailing
from util.postgres.db.models.tickers import Company_Business_Addresses as cbusiness
from util.postgres.db.models.tickers import Filings as filings

import pandas as pd
import os
import json
import pdb
import zipfile
from tqdm import tqdm
import time
import json
import pickle
import math
from util.postgres.db.create_schemas import create_schemas
create_schemas()

requests = requests_util()

current_file = os.path.basename(__file__)

def read_cik(self, cik: str = ''):
    if cik:
        cik.zfill(10)
    return cik

def nfilings_in_zip(zip_path):
    return len(zipfile.ZipFile(zip_path).infolist())
    
def read_zip_file(zip_path, nfilings, chunk_size):
    with zipfile.ZipFile(zip_path) as zip_ref:
        for i in range(0, nfilings, chunk_size):
            subm_obj = []
            info_chunk = zip_ref.infolist()[i:i + chunk_size]
            for info in info_chunk:
                if info.flag_bits & 0x1 == 0:
                    if not 'placeholder.txt' in info.filename:
                        with zip_ref.open(info, 'r') as f:
                            # You can read the contents of the file here
                            subm_obj.append(json.loads(f.read().decode('utf-8')))
            yield subm_obj
    

def clean_df(df: pd.DataFrame):
    df.replace(',','', regex=True, inplace=True)
    df.replace('\\\\','', regex=True, inplace=True)
    df.replace('/','', regex=True, inplace=True)

class Submissions():
    # Submissions:
    # List of all listed filing submissions made by the company.
    #  The 'recent' key contains a table of all accessionNumbers (filing identifiers) and the 
    # metadata needed to derive the url (to download the actual pdf).
    
    def __init__(self, crud_obj):
        # Nearly raw downloaded REST response (dict)
        self.filings: pd.DataFrame = pd.DataFrame()
        self.downloaded_data: dict = {}  
        self.downloaded_list: list = []  
        self.addresses_mailing: list = []
        self.addresses_business: list = []
        # Top-line company metadata
        self.meta_data: list = []
        # Descriptions for all of a company's filings
        self.filing_list: list = []
        self.cik: str = None
        self.crud_util = crud_obj
        print("Initiating submissions_df...")


    async def insert_submissions_from_zip(self, content_merged, zip_file: str = ''):
        success = False
        known_ciks = await self.crud_util.query_table(symbols, 'cik_str')
        if not known_ciks:
            return success
         
        # TODO: Still takes too long. Attempt to work with all objects as dataframes and insert
        # all in bulk. 
        if zip_file:
            try: 
                chunk_size = 1000
                nfilings = nfilings_in_zip(zip_file)
                filing = read_zip_file(zip_file, nfilings, chunk_size)
                pbar = tqdm(enumerate(filing), total=math.ceil(nfilings/chunk_size), desc="Performing Extract+Load of SEC Filings")
                for cnt, self.downloaded_list in pbar:
                    self.parse_response(content_merged, pbar)
                    await self.insert_table(pbar)
                    pbar.set_description(f"Processing Submissions: {100*chunk_size*(cnt+1)/(nfilings):.2f}%")

            except (Exception) as err:
                print(f"{err}")
        else:
            print('No zip file presented.')
        return success

    def parse_response(self, content_merged, pbar):

        t0 = time.time()
        self.downloaded_list = pd.DataFrame.from_dict(self.downloaded_list)
        self.downloaded_list['cik'] = self.downloaded_list['cik'].apply(lambda x: str(x).zfill(10))
        self.downloaded_list = pd.merge(self.downloaded_list, content_merged, on='cik', how='inner')

        self.downloaded_list['ticker'] = self.downloaded_list['ticker'].apply(lambda x: json.dumps(x))
        self.downloaded_list['exchanges'] = self.downloaded_list['exchanges'].apply(lambda x: json.dumps(x))
        self.downloaded_list['formerNames'] = self.downloaded_list['formerNames'].apply(lambda x: json.dumps(x))
        self.downloaded_list = self.downloaded_list.to_dict('records')
        
        # Set parsing rules and value checks, returning table of interest.
        for dct in self.downloaded_list:
            if 'filings' in dct.keys():
                cik = dct['cik']
                filings = dct.pop('filings')['recent']
                addresses = dct.pop('addresses')

                self.meta_data.append(dct)
                addresses['mailing'].update({'cik': cik})
                addresses['business'].update({'cik': cik})
                self.addresses_mailing.append(addresses['mailing'])
                self.addresses_business.append(addresses['business'])

                nrows = len(filings['accessionNumber'])
                filings.update({'cik': [cik] * nrows})
                filingsdf = pd.DataFrame(filings) 
                filingsd = filingsdf.to_dict(orient='tight', index=False)

                for row in filingsd['data']:
                    self.filing_list.append(dict(zip(filingsd['columns'], row)))

        self.downloaded_list = {}
        success = True
        return success

    async def insert_table(self, pbar) -> bool:
        success = False
        # Insert table(s) into database.
        if not self.filing_list:
            log.warning(f"No shares outstanding data to insert.")
        else:
            # Insert company filings    
            t0 = time.time()
            df = pd.DataFrame(self.filing_list)

            elements = ["cik", "accessionNumber", "filingDate", "reportDate", 
                    "acceptanceDateTime", "act", "form", "fileNumber", "filmNumber", 
                    "items", "core_type", "size", "isXBRL", "isInlineXBRL", 
                    "primaryDocument", "primaryDocDescription"]
            df = df[elements]

            clean_df(df)

            filings_dict = df.to_dict(orient='records')
            unique_elements = ["cik", "accessionNumber"]
            await self.crud_util.insert_rows_orm(filings, unique_elements, filings_dict)
            self.filing_list = []
            
        if not self.meta_data:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert company metadata
            t0 = time.time()
            df = pd.DataFrame(self.meta_data)

            elements = ['cik', 'name', 'tickers', 'exchanges', 'description', 'website', \
                     'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', \
                        'stateOfIncorporationDescription', 'ein', 'entityType', \
                            'sicDescription', 'ownerOrg', 'insiderTransactionForOwnerExists', \
                                'insiderTransactionForIssuerExists', 'phone', 'flags', 'formerNames']
            df = df[elements]
            clean_df(df)

            unique_elements = ["cik", "ein"]
            cmeta_dict = df.to_dict(orient='records')
            await self.crud_util.insert_rows_orm(cmeta, unique_elements, cmeta_dict)   
            self.meta_data = []

        if not self.addresses_mailing:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert mailing address
            t0 = time.time()
            df = pd.DataFrame(self.addresses_mailing)

            elements = ['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']
            df = df[elements]
            clean_df(df)

            unique_elements = ["cik"]
            cmail_dict = df.to_dict(orient='records')
            await self.crud_util.insert_rows_orm(cmailing, unique_elements, cmail_dict) 
            self. addresses_mailing = []

        if not self.addresses_business:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert business address
            t0 = time.time()
            df = pd.DataFrame(self.addresses_business)
            
            elements = ['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']
            df = df[elements]
            clean_df(df)

            unique_elements = ["cik"]
            cbusiness_dict = df.to_dict(orient='records')
            await self.crud_util.insert_rows_orm(cbusiness, unique_elements, cbusiness_dict)
            self.addresses_business = []
            
        self.filing_list
        success = True
        return success

