'''
Run BS4 to capture filing document htm files and extract novel information from it.
'''
import asyncio
import warnings
from util.logger import log
from util.requests_util import requests_util
from util.crud import crud as crud
from util.db.models.filings import Filings as company_filings
import pdb
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
from vectorize import add_data_to_vector_db

crud_util = crud()
requests = requests_util(rate_limit = 1.5)

uri_base = 'https://www.sec.gov/Archives/edgar/data/'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

def get_data(data):
    for dat in data:
        yield dat

async def query_files():
    columns_to_query = ['cik','accessionNumber','primaryDocument', 'primaryDocDescription', 'reportDate']
    query_match = ['6-K', '8-K', '10-K']
    # condition = {'query_col': "primaryDocDescription", 'query_match': ['6-K', '8-K', '10-K']}
    condition = {}
    response = await crud_util.query_table(company_filings, columns_to_query, condition)
    response_slim = [resp for resp in response if resp[3] in query_match]
    if response_slim:
        if isinstance(response_slim, list):
            filing_content_list = []
            cnt = 0
            for link in tqdm(response_slim, desc="Downloading Filing Document:"):
                cik = link[0]
                primaryDocDescription = link[3]
                reportDate = link[4]
                uriset = (cik.strip('0'), link[1].replace('-',''), link[2])
                uri = uri_base + '/'.join(uriset)
                resp = requests.get(url_in=uri, headers_in=header)
                pdb.set_trace()
                if resp:
                    soup = BeautifulSoup(resp.content, 'html5lib')
                    content_element ={
                                        'id': cnt,
                                        'fields': {
                                            'cik': cik,  
                                            'reportDate': reportDate,
                                            'uri': uri,
                                            'primaryDocDescription': primaryDocDescription, 
                                            'filing_content_string': soup.get_text().replace('\n',' ')
                                            }
                                        }
                    filing_content_list.append(content_element)
                    # pdb.set_trace()
                    cnt = cnt + 1
                    add_data_to_vector_db([content_element])
                else:
                    print(f"failed to get filing: \n{uri}")
            pdb.set_trace()
            add_data_to_vector_db(filing_content_list)
                

                # feed_iterable(get_data(data))
                # pdb.set_trace()
                # Fields: uri, primaryDocDescription, filing_content
                # Html content without the html tags. Very readable, but no formatting.
                # store filing_content in vector database along with ['cik','accessionNumber','primaryDocument', 'primaryDocDescription'] for reference

if __name__ == "__main__":
    t0 = time.time()

    asyncio.run(query_files())

    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")
