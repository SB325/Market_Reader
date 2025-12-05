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

url_tickers='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
          
async def get_facts(content_merged):
    crud_util = crud()
    msg = "Facts failed."
    facts = Facts(crud_util)
    t0 = time.time()
    vals = await facts.download_from_zip(
                os.path.join(
                os.path.dirname(__file__),
                '../',
                'companyfacts.zip')
            )
    facts.parse_response(content_merged)
    await facts.insert_table()

    t1 = time.time()
    msg = f"Facts time: {(t1-t0)/60} minutes."
    print(msg)
    return msg, vals

async def get_submissions(content_merged):
    crud_util = crud()
    msg = "Submissions failed."
    submissions = Submissions(crud_util)
    t0 = time.time()
    vals = await submissions.insert_submissions_from_zip(
                os.path.join(
                os.path.dirname(__file__),
                '../',
                'submissions.zip')
            )
    submissions.parse_response(content_merged)
    await submissions.insert_table()
    
    t1 = time.time()
    msg = f"Submissions time: {(t1-t0)/60} minutes."
    print(msg)
    return msg, vals

async def main():
    response = requests.get(url_in=url_tickers, headers_in=header)
    tickers_existing = list(response.json().values())

    tickerdata = await save_ticker_data(tickers_existing, False)

    for con in tickers_existing:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    df_existing = pd.DataFrame.from_dict(tickers_existing).rename(columns={'cik_str': 'cik'})

    # n = 500
    n=50
    for i in range(0, len(df_existing), n):
        chunk = df_existing.iloc[i:i + n]
        print(f"Processing chunk from index {i} to {i + n - 1}:")
        await get_facts(chunk)
        await get_submissions(chunk)

if __name__ == "__main__":
    t0 = time.time()

    print("Schema Created.")

    asyncio.run(main())
    
    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")
