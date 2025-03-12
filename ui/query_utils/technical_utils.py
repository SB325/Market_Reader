import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from util.crud_pg import crud
from util.postgres.db.models.tickers import Technicals, Symbols, Filings 
from util.time_utils import date_now_str, posix_now, to_posix, posix_to_datestr
from util.elastic.crud_elastic import crud_elastic

import asyncio
import pdb
import pandas as pd
from datetime import datetime

db = crud()
elastic = crud_elastic(verbose = True)

# Get price history for a ticker
async def get_ticker_price_history(ticker: str):
    try:
        price_history = await db.query_table(
            Technicals,
            query_col='ticker', 
            query_val=ticker)

    except BaseException as be:
        print(f"Error in price history query for {ticker}.")
    
    columns = Technicals.__table__.columns.keys()
    price_history_df = pd.DataFrame(price_history, columns=columns)
    
    return price_history_df

# Get list of tickers in Technicals table
async def technicals_ticker_stats():
    new_tickers_over_last_day = await db.query_table(
            Technicals,
            return_cols='ticker',
            query_col='datetime', 
            query_val=posix_now()-(60 * 60 * 24 * 1000), 
            query_operation='gt',
            unique_column_values='ticker')
    
    base_tickers = await db.query_table(Symbols, return_cols='ticker', unique_column_values='ticker')
    return len(base_tickers), len(new_tickers_over_last_day)

# Get list of fundamentals in Fundamentals table
async def fundamentals_ticker_stats():
    new_tickers_over_last_day = await db.query_table(
            Filings,
            return_cols=['cik', 'filingDate'],
            unique_column_values='cik')
    
    df = pd.DataFrame(new_tickers_over_last_day)
    df.columns = ['cik', 'date']
    unique_ciks = df['cik'].unique()

    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    tm = datetime.now().timetuple()
    year = tm.tm_year
    month = tm.tm_mon
    day = tm.tm_mday-1
    if day==0:
        month = month-1
        day = 28
    if month==0:
        month = 12
        year = year - 1
    recently_updated_ciks = df[df['date'] > pd.Timestamp(year, month, day)]['cik'].unique()

    return len(unique_ciks), len(recently_updated_ciks)

# Get list of tickers in Technicals table
async def news_ticker_stats():
    docs = elastic.count_documents()
    ndocuments = docs['count']
    # index = elastic.get_index(index='market_news')
    # docquery = elastic.retrieve_document(index='market_news')
    return ndocuments

# Get list of tickers in News table

if __name__ == "__main__":
    # val = asyncio.run(get_ticker_price_history('AAPL'))
    # val1, val2 = asyncio.run(fundamentals_ticker_stats())
    asyncio.run(news_ticker_stats())
    pdb.set_trace()
