import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import asyncio
from util.logger import log
from util.requests_util import requests_util
from util.postgres.db.models.tickers import Symbols as symbols
from util.postgres.db.models.tickers import SharesOutstanding as SharesOutstanding
from util.postgres.db.models.tickers import StockFloat as FloatTable
from util.postgres.db.models.tickers import Accounting as AccountingTable
from pipelines.fundamentals.get_ticker_list import save_ticker_data
from util.kafka.kafka import KafkaConsumer
import pandas as pd
import numpy as np

import json
import pdb
import time
import math
import pickle
from dotenv import load_dotenv
import gc  # invoke garbage collection with gc.collect() 
from util.crud_pg import crud as crud
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

url_tickers='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
topic = os.getenv("FACTS_KAFKA_TOPIC")
requests = requests_util()
consumer = KafkaConsumer([topic])

def read_cik(self, cik: str = ''):
    if cik:
        cik.zfill(10)
    return cik

def clean_df(df: pd.DataFrame):
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
        print("Initiating facts_df...")

    async def process_chunks(self, content_merged):
        success = False
        try: 
            while True:
                time.sleep(1)
                # consumer.recieve_continuous polls continuously until msg arrives
                self.downloaded_list = consumer.recieve_once()
                if not self.downloaded_list: # no message yet
                    continue
                self.parse_response(content_merged)
                await self.insert_table()
                log.info('Facts Data insert complete.')

        except (Exception) as err:
            print(f"{err}")
        success = True
        return success

    def parse_response(self, content_merged):
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

async def get_facts(content_merged):
    crud_util = crud()
    msg = "Facts failed."
    facts = Facts(crud_util)
    t0 = time.time()
    vals = await facts.process_chunks(content_merged)

    t1 = time.time()
    msg = f"Facts time: {(t1-t0)/60} minutes."
    print(msg)
    return msg, vals

async def main():
    response = requests.get(url_in=url_tickers, headers_in=header)
    tickers_existing = list(response.json().values())

    tickerdata = await save_ticker_data(tickers_existing, False)

    for con in tickers_existing:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    df_existing = pd.DataFrame.from_dict(tickers_existing).rename(columns={'cik_str': 'cik'})

    await get_facts(df_existing)

if __name__ == "__main__":
    t0 = time.time()

    print("Schema Created.")

    asyncio.run(main())
    
    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.") 