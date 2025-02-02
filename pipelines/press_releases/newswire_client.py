import sys
sys.path.append("../../")
from newswires import newswire
from util.postgres.db.models.tickers import Symbols as symbols
from util.crud_pg import crud
from util.elastic.models import news_article_model
from util.elastic.crud_elastic import crud_elastic
import pdb
import json
from dotenv import load_dotenv
import asyncio
import time

load_dotenv('db_creds.env')  
load_dotenv('.env')

nw = newswire()
crudpg = crud()
celastic = crud_elastic()
pdb.set_trace()
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
    for ticker in tickers:
        page = 0
        while not done:
            if nresults<20:
                done = True
            params = {'page': page,
                    'pageSize': 20,
                    'displayOutput': 'full',
                    'tickers': ticker,
                    'sort': 'created:desc',
                    'dateFrom': '2020-01-01'}
            print(f'Grabbing news history for {ticker}')
            results = nw.get_news_history(params = params)
            nresults = len(results)
            parse_for_elastic(results)

            start = time.time()
            celastic.bulk_insert_documents(results)
            print(f"{time.time() - start} seconds elapsed.")
            page = page + 1
            pdb.set_trace()
            

