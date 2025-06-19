import pdb
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

import asyncio
from util.postgres.db.models.tickers import Filings
from util.crud_pg import crud as crud
from util.requests_util import requests_util
from bs4 import Tag, NavigableString, BeautifulSoup
from tqdm import tqdm

requests = requests_util()
crud_util = crud()
header = header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

def get_content(soup):
    nav_strings = []
    element = soup.b.find_all_next(string=True)
    scrape = [val for val in 
        [word.replace('\xa0',' ')
            .replace('\u200b',' ')
            for word in element] 
            if not val.isspace()]
    
    return scrape

def download_filing(link: str):
    response = requests.get(url_in=link, headers_in=header)
    scrape = []
    try:
        soup = BeautifulSoup(response.text)
        scrape = get_content(soup)
    except:
        print(f"Failed to parse link:\n{link}")

    return scrape

def assemble_filings_link(cik: str, 
        accessionNumber: str, 
        primaryDocument: str
        ):
    link = "https://www.sec.gov/Archives/edgar/data/" \
        + f"{cik.lstrip('0')}/{accessionNumber.replace('-','')}/{primaryDocument}"

    return link

async def load_n_filings(nfilings: int, form: str = 'FORM 8-K'):
    filing_meta = await crud_util.query_table(Filings, 
        return_cols=['cik' , 'accessionNumber', 'primaryDocument'],
        query_col='primaryDocDescription',
        query_val=form,
        limit=nfilings
    )

    filings = []
    links = []
    for meta in filing_meta:
        cik = meta[0]
        accessionNumber = meta[1]
        primaryDocument = meta[2]

        links.append(assemble_filings_link(
                        cik, 
                        accessionNumber, 
                        primaryDocument))
    
        filings.append(download_filing(links[-1]))

    return filings, links

if __name__ == "__main__":
    filings_list, links = asyncio.run(load_n_filings(5,'FORM S-4') )
    pdb.set_trace()