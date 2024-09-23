'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
# import sys
# sys.path.append('../../')
from util.logger import log
from util.requests_util import requests_util
from pipelines.fundamentals.submissions import Submissions

import pandas as pd
import copy

from util.crud import crud as crud
from util.db.models.tickers import Symbols as SymbolTable

import pdb
from tqdm import tqdm

# requests = requests_util()
submissions = Submissions()
requests = requests_util()

crud = crud()
# cik = '0' * (10-len(cik)) + cik

# # url='https://www.sec.gov/files/company_tickers.json'
# url = f'https://data.sec.gov/submissions/CIK{cik}.json'
# # url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
url = f'https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip'
header = {'User-Agent': 'Mozilla/5.0'} #, \
# header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com'}

# output_filename = 'newdata.json'

if __name__ == "__main__":
    # cik_list = crud.query_table(SymbolTable, 'cik_str')
    # if cik_list:
    #     for cik in tqdm(cik_list[562:], desc="Capturing Filing MetaData:"):
    #         submissions.read_cik(cik)
    #         submissions.download_submission(cik)
    #         submissions.parse_response()
    #         submissions.insert_table()
    response = requests.get(url_in=url, headers_in=header)
    if response.ok:
        print('yaay')
        pdb.set_trace()
    else:
        print(f"{response.reason}")
        pdb.set_trace()
    