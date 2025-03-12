import sys
sys.path.append("../../")
from newswires import newswire
from util.postgres.db.models.tickers import Symbols as symbols
from util.crud_pg import crud
from util.elastic.crud_elastic import crud_elastic
from util.time_utils import to_posix
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
# celastic.delete_index(index='market_news')
# celastic.get_index(index='market_news')
# nw.search_ticker(index="market_news", ticker="AAPL")
# pdb.set_trace()

# load tickers
async def get_tickers() -> list:
    tickers = await crudpg.query_table(symbols, 'ticker')
    return tickers

def parse_for_elastic(data: dict):
    for dat in data:
        dat.pop('url')
        dat.pop('image')

def convert_date_to_posix(dateobj, datefmt: str):
    for date in dateobj:
        date['created'] =  to_posix(date['created'], datefmt)*1000
        date['updated'] =  to_posix(date['updated'], datefmt)*1000

def extract_channels(data: list):
    for dat in data:
        dat['channels'] = [val['name'] for val in dat['channels']]

earliest_date = "2020-01-01"
if __name__ == "__main__":
    datefmt = "%a, %d %b %Y %H:%M:%S %z"
    tickers = asyncio.run(get_tickers())
    pageSize = 99
    pbar = tqdm(tickers)
    for ticker in pbar:
        newTicker = True
        if newTicker:
            latest_data = nw.get_latest_news_from_ticker(ticker, default_latest=earliest_date)
            
            latest = latest_data.get(ticker, None)
            if not latest:
                latest = earliest_date

            newTicker = False
        page = 0
        nresults = pageSize
        done = False
        while not done:
            if nresults == 0:
                break
            if nresults < pageSize:
                print(f"Press release corpus has been updated for {ticker}")
                done = True
            pbar.set_description(f"Capturing {ticker} news data, page {page}. Last nresult: {nresults}")
            params = {'page': page,
                    'pageSize': pageSize,
                    'displayOutput': 'full',
                    'tickers': ticker,
                    'sort': 'created:asc',
                    'dateFrom': latest}
            results = nw.get_news_history(params = params)
            nresults = len(results)
            parse_for_elastic(results)
            convert_date_to_posix(results, datefmt)
            extract_channels(results)

            for result in results:
                # nsuccess = nw.to_db_bulk(ticker, results)
                ret = nw.to_db(ticker,result)
                #ObjectApiResponse({'_index': 'market_news', '_id': 'elTP4ZQBh3wAbWxnBBes', '_version': 1, 'result': 'created', '_shards': {'total': 2, 'successful': 2, 'failed': 0}, '_seq_no': 32, '_primary_term': 1})
            #pdb.set_trace()
            # print(f"{int(nsuccess[0])} Records successfully indexed. ")

            page = page + 1
            

