'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
# import sys
# sys.path.append('../../')
from util.logger import log
from util.crud import crud as crud
from util.db.models.tickers import Symbols as SymbolTable

import requests
import pdb
import json

url='https://www.sec.gov/files/company_tickers.json'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
output_filename = 'tickers.json'

crud_util = crud()

def save_ticker_data(data: dict, to_file: bool = True):
    if to_file:
        with open(output_filename,'w') as file:
            file.write(json.dumps(data))
    else:
        table = SymbolTable
        index_cols = ['cik_str']
        crud_util.insert_rows(table, index_cols, data)

if __name__ == "__main__":
    response = requests.get(url=url, headers=header)
    content = list(response.json().values())
    for con in content:
        cik = str(con['cik_str'])
        con['cik_str'] = '0' * (10-len(cik)) + cik

    save_ticker_data(content, False)