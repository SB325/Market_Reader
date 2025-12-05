import asyncio
from util.logger import log
from util.requests_util import requests_util
from util.postgres.db.models.tickers import Symbols as symbols
from util.postgres.db.models.tickers import SharesOutstanding as SharesOutstanding
from util.postgres.db.models.tickers import StockFloat as FloatTable
from util.postgres.db.models.tickers import Accounting as AccountingTable

import pandas as pd
import numpy as np
import os
import json
import pdb
import zipfile
from tqdm import tqdm
import time
import math
import pickle
from dotenv import load_dotenv
import gc  # invoke garbage collection with gc.collect() 
load_dotenv()
# from util.postgres.db.create_schemas import create_schemas
# create_schemas()

# from pyspark.sql import SparkSession

# spark_ip = os.environ.get("SPARK_IP")

# spark = SparkSession.builder \
#     .appName("MyApp") \
#     .master(f"spark://{spark_ip}:7077") \
#     .config("spark.executor.memory", "2g") \
#     .getOrCreate()

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

def read_zip_file(zip_path):
    filename = 'companyfacts.pkl' 
    if filename in os.listdir('pickles'):
        with open('pickles/' + filename, 'rb') as pickle_file:
            fact_obj = pickle.load(pickle_file)
    else:
        fact_obj = []
        with zipfile.ZipFile(zip_path) as zip_ref:
            for info in tqdm(zip_ref.infolist(), desc="Downloading Filing Data:"):
                # Check if the file is readable (not encrypted)
                if info.flag_bits & 0x1 == 0:
                    with zip_ref.open(info, 'r') as f:
                        # You can read the contents of the file here
                        fact_obj.append(json.loads(f.read().decode('utf-8')))

        with open('pickles/companyfacts.pkl', 'wb') as file:
            pickle.dump(fact_obj, file)
    
    return fact_obj

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
            print('no ticker symbols in database. Run get_ticker_list.py')
            return success
         
        # TODO: Still takes too long. Attempt to work with all objects as dataframes and insert
        # all in bulk. 
        if zip_file:
            try: 
                self.downloaded_list = read_zip_file(zip_file)
            except (Exception) as err:
                print(f"{err}")

            success = True
        else:
            print('No zip file presented.')
        return success

    async def parse_response(self, content_merged):

        success = False
        t0 = time.time()
        self.downloaded_list = pd.DataFrame.from_dict(self.downloaded_list)
        self.downloaded_list['cik'] = self.downloaded_list['cik'].apply(lambda x: str(x).zfill(10))
        self.downloaded_list = pd.merge(self.downloaded_list, content_merged, on='cik', how='inner')
        
        cik = self.downloaded_list['cik'].tolist()
        self.downloaded_list = self.downloaded_list.drop(['entityName'], axis=1)

        facts = self.downloaded_list['facts'].to_frame()

        # clear downloaded list from memory
        pdb.set_trace()
        self.downloaded_list.iloc[0:0]

        facts.insert(1, "cik", cik, True)

        dei = facts.facts.apply(lambda x: x.get('dei', None) if isinstance(x, dict) else {}).dropna()

        sharesoutstanding = dei.apply(lambda x: x.get('EntityCommonStockSharesOutstanding', None) if isinstance(x, dict) else {}).dropna()
        units = sharesoutstanding.apply(lambda x: x.get('units', None) if isinstance(x, dict) else {}).dropna()
        shares = units.apply(lambda x: x.get('shares', None) if isinstance(x, dict) else {}).dropna()
        
        for cnt, share in enumerate(shares):
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

        # clear dei_float from memory
        pdb.set_trace()
        dei_float = []

        # Accounting
        gaap = facts['facts'].apply(lambda x: x.get('us-gaap', None) if isinstance(x, dict) else {}).dropna()

        # clear dei and facts from memory
        pdb.set_trace()
        dei.iloc[0:0]
        pdb.set_trace()
        facts.iloc[0:0]

        # gaap = [ m['us-gaap'] for m in facts if 'us-gaap' in m.keys()]
        accounting = pd.DataFrame(gaap)
        pdb.set_trace()
        gaap.iloc[0:0]

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
        
        success = True
        return success

    async def insert_table(self) -> bool:
        
        success = False
        
        if not self.shares:
            log.warning(f"No shares outstanding data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.shares)
            elements = ['cik','end','val','accn','fy','fp','form','filed','frame']
            
            df = df[elements]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)
            
            so_dict = df.to_dict(orient='records')
            # so_dict = [val for val in so_dict if val['cik'] not in ciks]
            # await self.crud_util.insert_rows(SharesOutstanding, df)
            unique_elements = ["cik", "accn", "fy", "form"]
            await self.crud_util.insert_rows_orm(SharesOutstanding, unique_elements, so_dict[:3])
            
            print(f"{(time.time()-t0)/60} minutes elapsed on filings insertion.")
            self.shares = []

        if not self.float:
            log.warning(f"No float data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.float)
            
            elements = ['cik','end','val','accn','fy','fp','form','filed','frame','currency']
            df = df[elements]
            df['val'] = df['val'][df['val']<=np.iinfo(np.int64).max]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype('int64')
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)
            f_dict = df.to_dict(orient='records')
            
            unique_elements = ["cik", "accn", "fy", "form"]
            await self.crud_util.insert_rows_orm(FloatTable, unique_elements, f_dict)   
            print(f"{(time.time()-t0)/60} minutes elapsed on float data insertion.")
            self.float = []
        
        if not self.accounting_data:
            log.warning(f"No accounting data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.accounting_data)

            elements = ['cik','start','end','val','accn','fy','fp','form','filed','type','frame']
            df = df[elements]
            df['val'] = df['val'][df['val']<=np.iinfo(np.int64).max]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            await clean_df(df)
            a_dict = df.to_dict(orient='records')
            
            unique_elements = ["cik", "start", "end", "fy"]
            await self.crud_util.insert_rows_orm(AccountingTable, unique_elements, a_dict)
            print(f"{(time.time()-t0)/60} minutes elapsed on accounting data insertion.")
            self.accounting_data = []

        success = True
        return success