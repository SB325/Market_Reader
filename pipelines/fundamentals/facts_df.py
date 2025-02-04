import asyncio
from util.logger import log
from util.requests_util import requests_util
from util.postgres.db.models.tickers import Symbols as symbols
from util.postgres.db.models.tickers import SharesOutstanding as SharesOutstanding
from util.postgres.db.models.tickers import StockFloat as FloatTable
from util.postgres.db.models.tickers import Accounting as AccountingTable

import pandas as pd
import os
import json
import pdb
import zipfile
from tqdm import tqdm
import time
import math
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

class Facts():
    # Submissions:
    # List of all listed filing submissions made by the company.
    #  The 'recent' key contains a table of all accessionNumbers (filing identifiers) and the 
    # metadata needed to derive the url (to download the actual pdf).

    def __init__(self, crud_obj):
        # Nearly raw downloaded REST response (dict)
        self.download = []
        self.shares = []
        self.float = []
        self.accounting_data = []
        # Top-line company metadata
        self.meta_data: list = []
        # Descriptions for all of a company's filings
        self.filing_list: list = []
        self.cik: str = None
        self.crud_util = crud_obj

    async def download_from_zip(self, zip_file: str = ''):
        success = False
        known_ciks = await self.crud_util.query_table(symbols, 'cik_str')
        if not known_ciks:
            print('no tickers inserted.')
            return success
         
        # TODO: Still takes too long. Attempt to work with all objects as dataframes and insert
        # all in bulk. 
        if zip_file:
            
            with zipfile.ZipFile(zip_file) as myzip:
                for name in tqdm(myzip.namelist(), desc="Downloading Filing Data:"):
                    file = myzip.read(name)
                    try:
                        if len(file)>100:
                            f = json.loads(file)
                            if 'cik' in f.keys():
                                if known_ciks.count(str(f['cik']).zfill(10))==0: 
                                    continue
                            else:
                                continue
                            self.download.append(f)
                    except (Exception) as err:
                        pdb.set_trace()
                        print(f"{err}")

            success = True
        else:
            print('No zip file presented.')
        return success

    async def parse_response(self):
        success = False

        t0 = time.time()

        self.downloaded_list = pd.DataFrame.from_dict(self.download)
        self.downloaded_list['cik'] = self.downloaded_list['cik'].apply(lambda x: str(x).zfill(10))
        cik = self.downloaded_list['cik'].tolist()
        self.downloaded_list = self.downloaded_list.drop(['entityName'], axis=1)

        facts = self.downloaded_list['facts'].to_frame()
        facts.insert(1, "cik", cik, True)

        dei = facts['facts'].apply(lambda x: x['dei'] if 'dei' in x.keys() else {})

        key = 'EntityCommonStockSharesOutstanding'
        shares = dei.apply(lambda x: x[key]['units']['shares'] if key in x.keys() else {})

        for cnt, share in enumerate(shares):
            if not share:
                continue
            [s.update({'cik': cik[cnt]}) for s in share]
            self.shares.extend(share)
        [s.update({'frame': ''}) for s in self.shares if 'frame' not in s.keys()]

        dei_float = dei.apply(lambda x: x['EntityPublicFloat']['units'] if 'EntityPublicFloat' in x.keys() else {})
        
        for cnt,m in enumerate(dei_float):
            if m:
                currency = [q for q in m.keys()][0]
                [val.update({'currency': currency, 'cik': cik[cnt]}) for val in m[currency]]
                self.float.extend(m[currency])
        [f.update({'frame': ''}) for f in self.float if 'frame' not in f.keys()]

        # Accounting
        gaap = facts['facts'].apply(lambda x: x['us-gaap'] if 'us-gaap' in x.keys() else None)

        # gaap = [ m['us-gaap'] for m in facts if 'us-gaap' in m.keys()]
        accounting = pd.DataFrame(gaap)

        for cnt, units in enumerate(tqdm(accounting['facts'], desc = 'Accounting...')):
            if not units:
                continue
            types = units.keys()
            for typ in types:
                try:
                    addon = {'cik': cik[cnt], 'type': typ}
                    typ_dict = units[typ]
                    if not isinstance(typ_dict, dict):
                        if math.isnan(typ_dict):
                            continue
                    unts = typ_dict['units']
                    if 'USD' in unts.keys():
                        data = unts['USD']  # missing start key
                        # [dat.update({'start': ''}) for dat in data]
                    elif 'shares' in unts.keys():
                        data = unts['shares']
                    [acct.update(addon) for acct in data]
                    self.accounting_data.extend(data)  # list of dicts
                except:
                    pdb.set_trace()
        
        print(f"{(time.time()-t0)/60} minutes elapsed on initial download parsing.")
        
        self.download = []
        self.downloaded_list = []
        success = True
        return success

    async def insert_table(self) -> bool:
        
        success = False

        if not self.shares:
            log.warning(f"No shares outstanding data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.shares)
            df = df[['cik','end','val','accn','fy','fp','form','filed','frame']]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)
            await self.crud_util.insert_rows(SharesOutstanding, df)
            print(f"{(time.time()-t0)/60} minutes elapsed on filings insertion.")
            self.shares = []

        if not self.float:
            log.warning(f"No float data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.float)

            df = df[['cik','end','val','accn','fy','fp','form','filed','frame','currency']]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)
            await self.crud_util.insert_rows(FloatTable, df)   
            print(f"{(time.time()-t0)/60} minutes elapsed on float data insertion.")
            self.float = []

        
        if not self.accounting_data:
            log.warning(f"No accounting data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.accounting_data)

            df = df[['cik','start','end','val','accn','fy','fp','form','filed','type','frame']]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)

            await self.crud_util.insert_rows(AccountingTable, df)
            print(f"{(time.time()-t0)/60} minutes elapsed on accounting data insertion.")
            self.accounting_data = []

        success = True
        return success