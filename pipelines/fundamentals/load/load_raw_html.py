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
from util.postgres.db.models.tickers import Filings as company_filings
from util.postgres.db.models.fundamentals import FundamentalsArtifacts as Fundamentals
from pipelines.fundamentals.transform.explore_data import target_filings
from pipelines.fundamentals.transform.clean_html import clean_html

# from util.milvus.collection_model import collection_model_type
# from util.milvus.crud_milvus import crud_milvus
# from schema import filing_schema, field_params_dict
import re
from bs4 import BeautifulSoup   
import time
from tqdm import tqdm
import json
import pandas as pd
import copy

crud_util = crud()
# milvus = crud_milvus()
requests = requests_util(rate_limit = 0.11) # minimum period between requests (s)

uri_base = 'https://www.sec.gov/Archives/edgar/data/'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
header_vec = {'Content-Type': 'application/json'}

# c_name='rawFilings'

# try:
#     if not milvus.get_collection_state(c_name)['state'].value:
#         data_model = collection_model_type(
#                     **{
#                         "collection_name": c_name, 
#                         "model_schema": filing_schema,
#                         "index_params": field_params_dict,
#                     }
#                 )
        
#         milvus.create_collection(data_model) 
# except Exception as e:
#     pdb.set_trace()
#     print(e)

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

async def query_files():
    columns_to_query = ['cik','accessionNumber','primaryDocument', 'primaryDocDescription', 'reportDate', 'acceptanceDateTime']
    columns_to_insert = copy.deepcopy(columns_to_query)
    columns_to_insert.extend(['filename', 'content', 'uri'])
    columns_to_insert.remove('primaryDocument')

    response_db = await crud_util.query_table(
                        tablename=company_filings, 
                        return_cols=columns_to_query, 
                        )
    if response_db:
        if isinstance(response_db, list):
            cnt = 0
            for link in tqdm(response_db[cnt:], desc="Downloading Filing Document:"):
                cik = link[0]
                primaryDocDescription = link[3]
                reportDate = link[4]
                acceptanceDateTime = link[5]
                accessionNumber = link[1].replace('-','')

                # Check to see if this filing has already been loaded into milvus
                response = await crud_util.query_table(
                    tablename=Fundamentals, 
                    query_col='accessionNumber',
                    query_val=accessionNumber,
                    return_cols=['accessionNumber'], 
                    )
                # response = milvus.query(collection_name=c_name,
                #                 limit=1,
                #                 output_fields=['uri']
                #                 )

                # skip filings we already indexed
                if response:
                    continue
                    
                # get list of html dependencies and linked files.
                uriset = (cik.lstrip('0'), accessionNumber) #, link[2])
                uri = uri_base + '/'.join(uriset)

                resp = requests.get(url_in=uri, headers_in=header)

                if not resp:
                    print(f'Failed to download filing manifest for {uri}')

                content = pd.read_html(resp.content)

                try:
                    content_list = content[0]['Name'].tolist()
                    htm_list = [val for val in content_list if 'htm' in val.rsplit('.',1)[-1] ]
                    df = pd.DataFrame(htm_list, columns=['filename'])
                    df[['cik', 'accessionNumber']] = [[cik, accessionNumber]] * len(df)
                    htm_dict = df.to_dict(orient='records')
                except BaseException as be:
                    print('Failed to parse Content List! Errmsg:\n{be}')

                df = df[['cik', 'accessionNumber', 'filename']]

                # Post filing htmls to milvus
                filing_content_list = []
                for htm in htm_list:
                    uri_full = uri + '/' + htm
                    resp = requests.get(url_in=uri_full, headers_in=header)

                    # put resp.content into milvus, whether table or not
                    if not resp.content:
                        continue

                    content_element = {
                            'cik': cik,  
                            'reportDate': reportDate,
                            'acceptanceDateTime': acceptanceDateTime,
                            'accessionNumber': accessionNumber,
                            'uri': uri_full,
                            'primaryDocDescription': primaryDocDescription, 
                            'filename': htm,
                            'rawContent': resp.content
                        }
                        
                    clean_html(content_element)
                    
                    if '{}' != content_element['cleanContent']:
                        filing_content_list.append(content_element)
                
                await crud_util.insert_rows_orm(
                                Fundamentals, 
                                ["accessionNumber"], 
                                filing_content_list)
            
            # milvus.insert(data=filing_content_list)

if __name__ == "__main__":
    # t0 = time.time()

    asyncio.run(query_files())

    # t1 = time.time()

    # print(f"{(t1-t0)/60} minutes elapsed.")
