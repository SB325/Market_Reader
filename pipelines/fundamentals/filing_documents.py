'''
Run BS4 to capture filing document htm files and extract novel information from it.
'''
import asyncio
from util.logger import log
from util.requests_util import requests_util
from util.crud import crud as crud
from util.db.models.filings import Filings as company_filings
import pdb
from bs4 import BeautifulSoup
import time
from tqdm import tqdm

crud_util = crud()
requests = requests_util()

uri_base = 'https://www.sec.gov/Archives/edgar/data/'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

async def query_files():
    columns_to_query = ['cik','accessionNumber','primaryDocument', 'primaryDocDescription']
    response = await crud_util.query_table(company_filings, columns_to_query)
    if response:
        if isinstance(response, list):
            for link in tqdm(response, desc="Downloading Filing Document:"):
                uriset = (link[0].strip('0'), link[1].replace('-',''), link[2])
                uri = uri_base + '/'.join(uriset)
                resp = requests.get(url_in=uri, headers_in=header)
                soup = BeautifulSoup(resp.content, 'html5lib')

                filing_content = soup.get_text()  
                pdb.set_trace()
                # Fields: uri, primaryDocDescription, filing_content
                # Html content without the html tags. Very readable, but no formatting.
                # store filing_content in vector database along with ['cik','accessionNumber','primaryDocument'] for reference

if __name__ == "__main__":
    t0 = time.time()

    asyncio.run(query_files())

    t1 = time.time()

    print(f"{(t1-t0)/60} minutes elapsed.")