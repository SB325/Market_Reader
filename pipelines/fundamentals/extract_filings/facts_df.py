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

def read_cik(self, cik: str = ''):
    if cik:
        cik.zfill(10)
    return cik

def clean_df(df: pd.DataFrame):
    df.replace(',','', regex=True, inplace=True)
    df.replace('\\\\','', regex=True, inplace=True)
    df.replace('/','', regex=True, inplace=True)

def nfilings_in_zip(zip_path):
    return len(zipfile.ZipFile(zip_path).infolist())

def read_zip_file(zip_path, nfilings, chunk_size):
    with zipfile.ZipFile(zip_path) as zip_ref:
        for i in range(0, nfilings, chunk_size):
            fact_obj = []
            info_chunk = zip_ref.infolist()[i:i + chunk_size]
            for info in info_chunk:
                if info.flag_bits & 0x1 == 0:
                    if not 'placeholder.txt' in info.filename:
                        with zip_ref.open(info, 'r') as f:
                            # You can read the contents of the file here
                            fact_obj.append(json.loads(f.read().decode('utf-8')))
            yield fact_obj

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
        print("Initiating facts_df...")

    async def download_from_zip(self, content_merged, zip_file: str = ''):
        success = False
        known_ciks = await self.crud_util.query_table(symbols, 'cik_str')
        if not known_ciks:
            print('no ticker symbols in database. Run get_ticker_list.py')
            return success
         
        # TODO: Still takes too long. Attempt to work with all objects as dataframes and insert
        # all in bulk. 
        if zip_file:
            try: 
                chunk_size = 100
                nfilings = nfilings_in_zip(zip_file)
                filing = read_zip_file(zip_file, nfilings, chunk_size)
                pbar = tqdm(enumerate(filing), 
                            total=math.ceil(nfilings/chunk_size), 
                            desc="Performing Extract+Load of SEC Filings")
                for cnt, self.downloaded_list in pbar:
                    # if cnt<104:
                    #     continue
                    self.parse_response(content_merged, cnt)
                    await self.insert_table(cnt)
                    pbar.set_description(f"Processing Submissions: {100*chunk_size*(cnt+1)/(nfilings):.2f}%")

            except (Exception) as err:
                print(f"{err}")

            success = True
        else:
            print('No zip file presented.')
        return success

    def parse_response(self, content_merged, pbar):
        success = False
        t0 = time.time()
        self.downloaded_list = pd.DataFrame.from_dict(self.downloaded_list)
        self.downloaded_list['cik'] = self.downloaded_list['cik'].apply(lambda x: str(x).zfill(10))
        self.downloaded_list = pd.merge(self.downloaded_list, content_merged, on='cik', how='inner')
        
        cik = self.downloaded_list['cik'].tolist()
        self.downloaded_list = self.downloaded_list.drop(['entityName'], axis=1)

        facts = self.downloaded_list['facts'].to_frame()

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

        # Accounting
        gaap = facts['facts'].apply(lambda x: x.get('us-gaap', None) if isinstance(x, dict) else {}).dropna()

        # gaap = [ m['us-gaap'] for m in facts if 'us-gaap' in m.keys()]
        accounting = pd.DataFrame(gaap)

        for cnt, units in enumerate(accounting['facts']):
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
                    data = []    
                    # if any(['USD' in key for key in unts.keys()]):
                    #     key = [key for key in unts.keys() if 'USD' in key][0]
                    #     data = unts[key]  # missing start key
                    #     # [dat.update({'start': ''}) for dat in data]  #TODO: if start has value enter that into 
                    # elif any(['EUR' in key for key in unts.keys()]):
                    #     key = [key for key in unts.keys() if 'EUR' in key][0]
                    #     data = unts[key]  # missing start key
                    #     # [dat.update({'start': ''}) for dat in data]
                    # elif 'shares' in unts.keys():
                    #     data = unts['shares']
                    # else:
                    #     pdb.set_trace()
                    
                    key = [key for key in unts.keys()]
                    if len(key)>1:
                        [data.extend(unts[k]) for k in key]
                    else:
                        data = unts[key[0]]
                    [acct.update(addon) for acct in data]
                    # pdb.set_trace()
                    self.accounting_data.extend(data)  # list of dicts
                except:
                    pdb.set_trace()
                
        success = True
        return success

    async def insert_table(self, pbar) -> bool:
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
            clean_df(df)
            
            so_dict = df.to_dict(orient='records')
            # so_dict = [val for val in so_dict if val['cik'] not in ciks]
            # self.crud_util.insert_rows(SharesOutstanding, df)
            unique_elements_so = ["cik", "accn", "fy", "form"]
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
            clean_df(df)
            f_dict = df.to_dict(orient='records')
            
            unique_elements_f = ["cik", "accn", "fy", "form"]
            self.float = []

        if not self.accounting_data:
            log.warning(f"No accounting data to insert.")
        else:
            t0 = time.time()
            df = pd.DataFrame(self.accounting_data)

            elements = ['cik','end','val','accn','fy','fp','form','filed','type','frame']
            df = df[elements]
            df['val'] = df['val'][df['val']<=np.iinfo(np.int64).max]
            df['val'] = df['val'].fillna(0)
            df['val'] = df['val'].astype(int)
            df['fy'] = df['fy'].fillna(0)
            df['fy'] = df['fy'].astype(int)
            clean_df(df)
            a_dict = df.to_dict(orient='records')

            unique_elements_a = ["cik", "end", "fy"] # why are these columns unique elements?

            last_accounting_element = await self.crud_util.query_table(AccountingTable, 
                                                    query_col='accn', 
                                                    query_val=a_dict[-1]['accn'])
            # if data not present, insert it here.
            if not last_accounting_element:
                await self.crud_util.insert_rows_orm(SharesOutstanding, unique_elements_so, so_dict[:3])
                await self.crud_util.insert_rows_orm(FloatTable, unique_elements_f, f_dict)  
                await self.crud_util.insert_rows_orm(AccountingTable, unique_elements_a, a_dict)
            self.accounting_data = []
        success = True
        return success