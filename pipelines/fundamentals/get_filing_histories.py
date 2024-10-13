'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import asyncio
from util.logger import log
from util.requests_util import requests_util
from pipelines.fundamentals.submissions_df import Submissions
from pipelines.fundamentals.facts_df import Facts
from pipelines.fundamentals.get_ticker_list import save_ticker_data
import pdb
import time
from util.crud import crud as crud

requests = requests_util()
crud_util = crud()

url_tickers='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
          
async def get_facts():
    msg = "Facts failed."
    facts = Facts(crud_util)
    t0 = time.time()
    vals = await asyncio.gather(facts.download_from_zip('companyfacts.zip'), \
                                facts.parse_response(), \
                                facts.insert_table())
    # if await facts.download_from_zip('companyfacts.zip'):
    #     if await facts.parse_response():
    #         if await facts.insert_table():
    #             pass
    #         else:
    #             print('Facts not inserted into table.')
    #     else:
    #         print('Facts not parsed.')
    # else:
    #     print('Facts not downloaded from zip.')
    t1 = time.time()
    del facts
    msg = f"Facts time: {(t1-t0)/60} minutes."
    return msg, vals

async def get_submissions():
    msg = "Submissions failed."
    submissions = Submissions(crud_util)
    t0 = time.time()
    vals = await asyncio.gather(submissions.insert_submissions_from_zip('companyfacts.zip'), \
                                submissions.parse_response(), \
                                submissions.insert_table())
    # if submissions.insert_submissions_from_zip('submissions.zip'):
    #     if submissions.parse_response():
    #         if submissions.insert_table():
    #             pass
    #         else:
    #             print('Submissions not inserted into table.')
    #     else:
    #         print('Submissions not parsed.')
    # else:
    #     print('Submissions not downloaded from zip.')
    t1 = time.time()
    del submissions
    msg = f"Submissions time: {(t1-t0)/60} minutes."
    return msg, vals

async def main():
    response = requests.get(url_in=url_tickers, headers_in=header)
    content = list(response.json().values())
    for con in content:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    first_task = await save_ticker_data(content, False)
    await asyncio.gather(get_facts(), get_submissions())

if __name__ == "__main__":
    t0 = time.time()

    print("Schema Created.")

    asyncio.run(main())
    
    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")
