import sys
sys.path.append("../../")
from newswires import newswire
from util.postgres.db.models.tickers import Symbols as symbols
from util.crud_pg import crud
from util.elastic.crud_elastic import crud_elastic

from tqdm import tqdm
import pdb
import json
from dotenv import load_dotenv
import asyncio
import time

load_dotenv('.env')

celastic = crud_elastic()
nw = newswire(celastic)  # Constructor creates index and mapping
crudpg = crud()

# nw.crud.delete_index('market_news')
# celastic.get_mappings()
# nw.search_ticker(index="market_news", ticker="AAPL")
# pdb.set_trace()

# load tickers
async def get_tickers() -> list:
    tickers = await crudpg.query_table(symbols, 'ticker')
    return tickers

def parse_for_elastic(data: dict):
    for dat in data:
        dat.pop('url')
        dat.pop('tags')
        dat.pop('image')

if __name__ == "__main__":

    tickers = asyncio.run(get_tickers())
    done = False
    nresults = 20
    pbar = tqdm(tickers)
    for ticker in pbar:
        latest = nw.get_latest_news_from_ticker(ticker)

        page = 0
        while not done:
            pbar.set_description(f"Capturing {ticker} news data, page {page}")
            if nresults<20:
                done = True
            params = {'page': page,
                    'pageSize': 20,
                    'displayOutput': 'full',
                    'tickers': ticker,
                    'sort': 'created:desc',
                    'dateFrom': latest}
            results = nw.get_news_history(params = params)
            nresults = len(results)
            parse_for_elastic(results)

            # start = time.time()
            nw.to_db_bulk(ticker, results)
            # print(f"{time.time() - start} seconds elapsed.")

            page = page + 1
            # val = celastic.search_ticker(index="market_news", ticker="AAPL")
            pdb.set_trace()   
            

