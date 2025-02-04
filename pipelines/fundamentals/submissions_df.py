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
from util.postgres.db.create_schemas import create_schemas

create_schemas()
requests = requests_util()

current_file = os.path.basename(__file__)

async def read_cik(self, cik: str = ''):
    if cik:
        cik.zfill(10)
    return cik

async def clean_df(df: pd.DataFrame):
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

    async def insert_submissions_from_zip(self, zip_file: str = ''):
        success = False
        known_ciks = await self.crud_util.query_table(symbols, 'cik_str')
        if not known_ciks:
            return success
         
        # TODO: Still takes too long. Attempt to work with all objects as dataframes and insert
        # all in bulk. 
        if zip_file:
            self.downloaded_list = []
            with zipfile.ZipFile(zip_file) as myzip:
                # try:
                for name in tqdm(myzip.namelist(), desc="Capturing Filing MetaData:"):
                    file = myzip.read(name)
                    try:
                        if len(file)>100:
                            self.downloaded_list.append(json.loads(file))
                    except:
                        pdb.set_trace()
            t0 = time.time()
            self.downloaded_list = [m for m in self.downloaded_list if 'cik' in m.keys()]
            self.downloaded_list = pd.DataFrame.from_dict(self.downloaded_list)
            self.downloaded_list['cik'] = self.downloaded_list['cik'].apply(lambda x: str(x).zfill(10))
            self.downloaded_list['tickers'] = self.downloaded_list['tickers'].apply(lambda x: json.dumps(x))
            self.downloaded_list['exchanges'] = self.downloaded_list['exchanges'].apply(lambda x: json.dumps(x))
            self.downloaded_list['formerNames'] = self.downloaded_list['formerNames'].apply(lambda x: json.dumps(x))
            self.downloaded_list = self.downloaded_list.to_dict('records')
            self.downloaded_list = [m for m in self.downloaded_list if m['cik'] in known_ciks ]
            print(f"{(time.time()-t0)/60} minutes elapsed on initial download parsing.")
            success = True
        else:
            print('No zip file presented.')
        return success

    async def parse_response(self):
        success = False
        # Set parsing rules and value checks, returning table of interest.
        for dct in tqdm(self.downloaded_list, desc='Extracting Metadata'):
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

        success = True
        return success

    async def insert_table(self) -> bool:
        success = False
        # Insert table(s) into database.
        if not self.filing_list:
            log.warning(f"No filings data to insert for cik {self.cik}.")
        else:
            # Insert company filings    
            t0 = time.time()
            df = pd.DataFrame(self.filing_list)

            df = df[['cik', 'accessionNumber', 'filingDate', 'reportDate', 'acceptanceDateTime', \
                'act', 'form', 'fileNumber', 'filmNumber', 'items', 'core_type', 'size', \
                'isXBRL', 'isInlineXBRL', 'primaryDocument', 'primaryDocDescription']]
            await clean_df(df)
            await self.crud_util.insert_rows(filings, df)
            print(f"{(time.time()-t0)/60} minutes elapsed on filings insertion.")
            self.filing_list = []
            
        if not self.meta_data:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert company metadata
            t0 = time.time()
            df = pd.DataFrame(self.meta_data)

            df = df[['cik', 'name', 'tickers', 'exchanges', 'description', 'website', \
                     'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', \
                        'stateOfIncorporationDescription', 'ein', 'entityType', \
                            'sicDescription', 'ownerOrg', 'insiderTransactionForOwnerExists', \
                                'insiderTransactionForIssuerExists', 'phone', 'flags', 'formerNames']]
            await clean_df(df)
            await self.crud_util.insert_rows(cmeta, df)   
            print(f"{(time.time()-t0)/60} minutes elapsed on metadata insertion.")
            self.meta_data = []

        if not self.addresses_mailing:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert mailing address
            t0 = time.time()
            df = pd.DataFrame(self.addresses_mailing)

            df = df[['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']]
            await clean_df(df)
            await self.crud_util.insert_rows(cmailing, df) 
            print(f"{(time.time()-t0)/60} minutes elapsed on mailing addr insertion.")
            self. addresses_mailing = []

        if not self.addresses_business:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert business address
            t0 = time.time()
            df = pd.DataFrame(self.addresses_business)
            
            df = df[['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']]
            await clean_df(df)
            await self.crud_util.insert_rows(cbusiness, df)
            print(f"{(time.time()-t0)/60} minutes elapsed on business addr insertion.")
            self.addresses_business = []
            
        self.downloaded_list = []
        self.filing_list
        success = True
        return success

