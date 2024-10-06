'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
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
submissions = Submissions(crud_util)
facts = Facts(crud_util)

url_tickers='https://www.sec.gov/files/company_tickers.json'
# url = f'https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

# header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com',
          
def get_facts():
    msg = "Facts failed."
    t0 = time.time()
    if facts.download_from_zip('companyfacts.zip'):
        if facts.parse_response():
            if facts.insert_table():
                pass
            else:
                print('Facts not inserted into table.')
        else:
            print('Facts not parsed.')
    else:
        print('Facts not downloaded from zip.')
    t1 = time.time()
    msg = f"Facts time: {(t1-t0)/60} minutes."
    return msg

def get_submissions():
    msg = "Submissions failed."
    t0 = time.time()
    if submissions.insert_submissions_from_zip('submissions.zip'):
        if submissions.parse_response():
            if submissions.insert_table():
                pass
            else:
                print('Submissions not inserted into table.')
        else:
            print('Submissions not parsed.')
    else:
        print('Submissions not downloaded from zip.')
    t1 = time.time()
    msg = f"Submissions time: {(t1-t0)/60} minutes."
    return msg

if __name__ == "__main__":
    t0 = time.time()

    print("Schema Created.")

    response = requests.get(url_in=url_tickers, headers_in=header)
    content = list(response.json().values())
    for con in content:
        con['cik_str'] = str(con['cik_str']).zfill(10)

    print(save_ticker_data(content, False))
    print(get_facts())
    print(get_submissions())
    

    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")
