'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import asyncio
from util.logger import log
from util.crud import crud as crud
from util.db.models.tickers import Symbols as SymbolTable
import pandas as pd
import requests
import pdb
import json
import time

url='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
output_filename = 'tickers.json'

crud_util = crud()

async def clean_df(df: pd.DataFrame):
    df.replace(',','', regex=True, inplace=True)
    df.replace('\\\\','', regex=True, inplace=True)
    df.replace('/','', regex=True, inplace=True)

async def save_ticker_data(data: dict, to_file: bool = True):
    msg = "Tickers failed."
    t0 = time.time()
    if to_file:
        with open(output_filename,'w') as file:
            file.write(json.dumps(data))
    else:
        table = SymbolTable
        index_cols = ['cik_str']
        df = pd.DataFrame(data)
        df.drop_duplicates(subset=['cik_str'], keep='first',inplace=True)
        await clean_df(df)
        await crud_util.insert_rows(table, df)

    t1 = time.time()
    msg = f"Tickers time: {(t1-t0)/60} seconds."
    return msg

if __name__ == "__main__":
    response = requests.get(url=url, headers=header)
    content = list(response.json().values())
    for con in content:
        cik = str(con['cik_str'])
        con['cik_str'] = '0' * (10-len(cik)) + cik
    df = pd.DataFrame(content)

    asyncio.run(save_ticker_data(df, False))