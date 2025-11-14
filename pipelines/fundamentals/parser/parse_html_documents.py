'''
Run BS4 to capture filing document htm files and extract novel information from it.
'''
import asyncio
import warnings
import sys, os
import pdb
sys.path.append(os.path.join(os.getcwd())) #, '../../'))
from util.logger import log
from util.requests_util import requests_util
from util.crud_pg import crud as crud
from util.elastic.crud_elastic import crud_elastic as crud_elastic
from util.postgres.db.models.tickers import Filings as company_filings
from util.postgres.db.models.fundamentals import FundamentalsArtifacts as fundamentals_artifacts
import re
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import json
import pandas as pd
# from vectorize.vectorize import add_data_to_vector_db

crud_util = crud()
elastic = crud_elastic()
requests = requests_util(rate_limit = 1.5)

uri_base = 'https://www.sec.gov/Archives/edgar/data/'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
header_vec = {'Content-Type': 'application/json'}

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

def get_data(data):
    for dat in data:
        yield dat

async def query_files():
    columns_to_query = ['cik','accessionNumber','primaryDocument', 'primaryDocDescription', 'reportDate', 'acceptanceDateTime']
    # query_match = ['10-K']
    # condition = {'query_col': "primaryDocDescription", 'query_match': ['6-K', '8-K', '10-K']}
    # https://www.sec.gov/Archives/edgar/data/1675149/000095017025100979/aa-20250630.htm

    response_db = await crud_util.query_table(
                        tablename=company_filings, 
    4                   return_cols=columns_to_query, 
                        )
    # '0001318605' - tesla
    # '0000354950' - home depot
    # response_slim = [resp for resp in response if (resp[3] in query_match and '0000354950' in resp[0])]
    if response_db:
        if isinstance(response_db, list):
            filing_content_list = []
            cnt = 0
            for link in tqdm(response_db[cnt:], desc="Downloading Filing Document:"):
                cik = link[0]
                primaryDocDescription = link[3]
                reportDate = link[4]
                acceptanceDateTime = link[5]
                accessionNumber = link[1].replace('-','')

                # get list of html dependencies and linked files.
                uriset = (cik.lstrip('0'), accessionNumber) #, link[2])
                uri = uri_base + '/'.join(uriset)

                # Check to see if this accessionNumber has already been captured
                response = await crud_util.query_table(
                                fundamentals_artifacts, 
                                return_cols=['accessionNumber'],
                                query_col='accessionNumber', 
                                query_val=accessionNumber,
                                unique_column_values='accessionNumber',
                                )
                # skip filings we already indexed
                if response:
                    continue

                resp = requests.get(url_in=uri, headers_in=header)

                if not resp:
                    print(f'Failed to download filing manifest for {uri}')

                content = pd.read_html(resp.content)
                try:
                    content_list = content[0]['Name'].tolist()
                    htm_list = [val for val in content_list if val.rsplit('.',1)[-1] == 'htm']
                    df = pd.DataFrame(htm_list, columns=['filename'])
                    df[['cik', 'accessionNumber']] = [[cik, accessionNumber]] * len(df)
                    htm_dict = df.to_dict(orient='records')
                except BaseException as be:
                    print('Failed to parse Content List! Errmsg:\n{be}')

                df = df[['cik', 'accessionNumber', 'filename']]
                # Post filing artifacts to db
                response = await crud_util.insert_rows_orm(
                                fundamentals_artifacts, 
                                index_elements=['accessionNumber', 'filename'],
                                data=df, 
                                )
                
                for htm in htm_list:
                    uri_full = uri + '/' + htm
                    resp = requests.get(url_in=uri_full, headers_in=header)

                    # put resp.content into elasticdb, whether table or not
                    if not resp.content()
                        continue
                    content_element = {
                                        'id': cnt,
                                        'fields': {
                                            'cik': cik,  
                                            'reportDate': reportDate,
                                            'acceptanceDateTime': acceptanceDateTime,
                                            'accessionNumber': accessionNumber,
                                            'uri': uri_full,
                                            'primaryDocDescription': primaryDocDescription, 
                                            'filename': htm,
                                            'content': resp.content
                                            }
                                        }
                filing_content_list.append(content_element)
                
            pdb.set_trace()

if __name__ == "__main__":
    # t0 = time.time()

    asyncio.run(query_files())

    # t1 = time.time()

    # print(f"{(t1-t0)/60} minutes elapsed.")
