import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import asyncio
from util.requests_util import requests_util
from util.postgres.db.models.tickers import Symbols as symbols
from util.postgres.db.models.tickers import Company_Meta as cmeta
from util.postgres.db.models.tickers import Company_Mailing_Addresses as cmailing
from util.postgres.db.models.tickers import Company_Business_Addresses as cbusiness
from util.postgres.db.models.tickers import Filings as filings
from pipelines.fundamentals.get_ticker_list import save_ticker_data
from util.kafka.kafka import KafkaConsumer
import pandas as pd
from dotenv import load_dotenv
import json
import pdb
from tqdm import tqdm
import time
import json
import pickle
import math
from util.postgres.db.create_schemas import create_schemas
from util.crud_pg import crud as crud
from util.otel import otel_tracer, otel_metrics, otel_logger

otraces = otel_tracer()
ometrics = otel_metrics()
ologs = otel_logger()

create_schemas()
load_dotenv(override=True)
load_dotenv('util/kafka/.env')

url_tickers='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

topic = os.getenv("SUBMISSIONS_KAFKA_TOPIC")
consumer = KafkaConsumer(topic=[topic])
requests = requests_util()

ometrics.create_meter(
            meter_name = 'submissions_stream_unzip',
            meter_type = "AsynchronousUpDownCounter",
            description = 'As distributed transform/load replicas process \
                filing data, this value will decline.',
            )

def read_cik(self, cik: str = ''):
    if cik:
        cik.zfill(10)
    return cik

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

    async def process_chunks(self, content_merged):
        success = False
        try: 
            while True:
                time.sleep(1)
                # consumer.recieve_continuous polls continuously until msg arrives
                with otraces.set_span('transform_submissions_stream_unzip') as span:
                    self.downloaded_list = consumer.recieve_once()
                    ometrics.update_up_down_counter(counter_name='submissions_stream_unzip', change_by=-1)
                    if not self.downloaded_list: # no message yet
                        print('No message yet.')
                        continue
                    self.parse_response(content_merged)
                with otraces.set_span(f'load_submissions_stream_unzip') as span:
                    await self.insert_table()
                log.info('Submissions Data insert complete.')

        except (Exception) as err:
            print(f"{err}")
        success = True
        return success

    def parse_response(self, content_merged):

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

    async def insert_table(self) -> bool:
        success = False
        # Insert table(s) into database.
        if not self.filing_list:
            log.warning(f"No shares outstanding data to insert.")
        else:
            # Insert company filings    
            df = pd.DataFrame(self.filing_list)

            elements = ["cik", "accessionNumber", "filingDate", "reportDate", 
                    "acceptanceDateTime", "act", "form", "fileNumber", "filmNumber", 
                    "items", "core_type", "size", "isXBRL", "isInlineXBRL", 
                    "primaryDocument", "primaryDocDescription"]
            df = df[elements]

            clean_df(df)

            filings_dict = df.to_dict(orient='records')
            filings_unique_elements = ["cik", "accessionNumber"]
            
        if not self.meta_data:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert company metadata
            df = pd.DataFrame(self.meta_data)

            elements = ['cik', 'name', 'tickers', 'exchanges', 'description', 'website', \
                     'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', \
                        'stateOfIncorporationDescription', 'ein', 'entityType', \
                            'sicDescription', 'ownerOrg', 'insiderTransactionForOwnerExists', \
                                'insiderTransactionForIssuerExists', 'phone', 'flags', 'formerNames']
            df = df[elements]
            clean_df(df)

            cmeta_unique_elements = ["cik", "ein"]
            cmeta_dict = df.to_dict(orient='records')
        if not self.addresses_mailing:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert mailing address
            df = pd.DataFrame(self.addresses_mailing)

            elements = ['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']
            df = df[elements]
            clean_df(df)

            cmail_unique_elements = ["cik"]
            cmail_dict = df.to_dict(orient='records')
            

        if not self.addresses_business:
            log.warning(f"No meta_data to insert for cik {self.cik}")
        else:
            # Insert business address
            df = pd.DataFrame(self.addresses_business)
            
            elements = ['cik','street1', 'street2', 'city', 'stateOrCountry', 'zipCode',
                    'stateOrCountryDescription']
            df = df[elements]
            clean_df(df)

            cbusiness_unique_elements = ["cik"]
            cbusiness_dict = df.to_dict(orient='records')

        await self.crud_util.insert_rows_orm(filings, filings_unique_elements, filings_dict)
        await self.crud_util.insert_rows_orm(cmeta, cmeta_unique_elements, cmeta_dict)   
        await self.crud_util.insert_rows_orm(cmailing, cmail_unique_elements, cmail_dict) 
        await self.crud_util.insert_rows_orm(cbusiness, cbusiness_unique_elements, cbusiness_dict)
        
        self.filing_list = []
        self.meta_data = []
        self. addresses_mailing = []
        self.filing_list = []
        self.addresses_business = []
        success = True
        return success

async def get_submissions(content_merged):
    crud_util = crud()
    msg = "Submissions failed."
    submissions = Submissions(crud_util)
    vals = await submissions.process_chunks(content_merged)
    
    return msg, vals

async def main():
    response = requests.get(url_in=url_tickers, headers_in=header)
    tickers_existing = list(response.json().values())

    tickerdata = await save_ticker_data(tickers_existing, False)

    for con in tickers_existing:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    df_existing = pd.DataFrame.from_dict(tickers_existing).rename(columns={'cik_str': 'cik'})

    await get_submissions(df_existing)

if __name__ == "__main__":
    asyncio.run(main())