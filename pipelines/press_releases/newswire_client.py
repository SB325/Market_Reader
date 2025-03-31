import sys
sys.path.append("../../")
from newswires import newswire
from util.postgres.db.models.tickers import Symbols as symbols
from util.crud_pg import crud
from util.elastic.crud_elastic import crud_elastic
from util.time_utils import to_posix, posix_to_datestr
from tqdm import tqdm
import pdb
import json
from dotenv import load_dotenv
import asyncio
import time
# import argparse
import schedule
from util.webhook_server.push_notify import push_notify

load_dotenv('.env')

celastic = crud_elastic()
nw = newswire(celastic)  # Constructor creates index and mapping
crudpg = crud()
pn = push_notify()

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

def run():
    start_time = time.time()
    start_time_str = posix_to_datestr(int(start_time),"%a, %d %b %Y %H:%M:%S %z") 

    earliest_date = "2020-01-01"
    datefmt = "%a, %d %b %Y %H:%M:%S %z"
    tickers = asyncio.run(get_tickers())
    pageSize = 100
    pbar = tqdm(tickers)
    for ticker in pbar:
        newTicker = True
        if newTicker:
            latest_data = nw.get_latest_news_from_ticker(ticker)
            if not latest_data:
                latest = earliest_date
            else:
                latest = posix_to_datestr(latest_data['created'], "%Y-%m-%d")
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
            if page>99:
                print('Query too large for paging limits. Exiting. Will complete gathering news for this ticker on next run.')
                break
            pbar.set_description(f"Checking for updated {ticker} news data. Page {page}")
            params = {'page': page,
                    'pageSize': pageSize,
                    'displayOutput': 'full',
                    'tickers': ticker,
                    'sort': 'created:asc',
                    'dateFrom': latest}
            
            results = nw.get_news_history(params = params)
            
            # only index news that are newer than the ones we already have
            if not latest_data:
                fresh_results = results
            else:
                fresh_results = [result for result in results if latest_data['created']<to_posix(result['created'], "%a, %d %b %Y %H:%M:%S %z")*1000]
            if not fresh_results:
                print(f"No new news for {ticker}")
                done = True
            else:
                parse_for_elastic(fresh_results)
                convert_date_to_posix(fresh_results, datefmt)
                extract_channels(fresh_results)

                nsuccess = nw.to_db_bulk(ticker, fresh_results)
                # pdb.set_trace()
                # print(f"{int(nsuccess[0])} Records successfully indexed. ")

            page = page + 1
    
    duration = (time.time() - start_time)/60
    _ = pn.send(title='News_Index_Updated',
                        message=f"Newsire Index has been updated. Began at {start_time_str}, lasted {duration:.2f} minutes."
                        )
    
if __name__ == "__main__":
    print("Running Newswire_database_populater.")
    schedule.every().day.at("21:00").do(run) 

    while True:
        schedule.run_pending()
        time.sleep(3600)