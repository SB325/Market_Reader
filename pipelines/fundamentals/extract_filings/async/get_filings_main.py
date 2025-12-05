'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import pdb
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import asyncio
from util.logger import log

from util.requests_util import requests_util
from pipelines.fundamentals.extract_filings.submissions_df import Submissions
from pipelines.fundamentals.extract_filings.facts_df import Facts
from pipelines.fundamentals.get_ticker_list import save_ticker_data
from util.postgres.db.models.tickers import Symbols as Symbols

import pandas as pd
import time
from util.crud_pg import crud as crud

requests = requests_util()
crud_util = crud()

url_tickers='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
          
async def get_facts(content_merged):
    msg = "Facts failed."
    facts = Facts(crud_util)
    t0 = time.time()
    vals = await asyncio.gather(facts.download_from_zip(
                                        os.path.join(
                                            os.path.dirname(__file__),
                                            '../',
                                            'companyfacts.zip')
                                        ), 
                                facts.parse_response(content_merged), 
                                facts.insert_table())

    t1 = time.time()
    del facts
    msg = f"Facts time: {(t1-t0)/60} minutes."
    print(msg)
    return msg, vals

async def get_submissions(content_merged):
    msg = "Submissions failed."
    submissions = Submissions(crud_util)
    t0 = time.time()
    vals = await asyncio.gather(submissions.insert_submissions_from_zip(
                                        os.path.join(
                                            os.path.dirname(__file__),
                                            '../',
                                            'submissions.zip')
                                        ),
                                submissions.parse_response(content_merged), \
                                submissions.insert_table())
    
    t1 = time.time()
    del submissions
    msg = f"Submissions time: {(t1-t0)/60} minutes."
    print(msg)
    return msg, vals

async def main():
    response = requests.get(url_in=url_tickers, headers_in=header)
    content = list(response.json().values())
    base_tickers = await crud_util.query_table(Symbols, 
        return_cols='ticker', 
        unique_column_values='ticker'
    )
    base_tickers = [val[0] for val in base_tickers]
    df_base = pd.DataFrame(base_tickers, columns=['ticker'])
    df_content = pd.DataFrame.from_dict(content)
    merged_df = pd.merge(df_content, df_base, on='ticker', how='inner')

    content_merged = merged_df.to_dict(orient='records')
    for con in content_merged:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    content_merged = pd.DataFrame.from_dict(content_merged).rename(columns={'cik_str': 'cik'})

    # first_task = await save_ticker_data(content, False)
    await asyncio.gather(get_facts(content_merged))
    # await asyncio.gather(get_submissions(content_merged))
    # ,
    #                     

if __name__ == "__main__":
    t0 = time.time()

    print("Schema Created.")

    asyncio.run(main())
    
    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")
