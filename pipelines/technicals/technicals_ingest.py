import sys
# sys.path.append('..')
from source_data_interface.technicals_io import technicals
from source_data_interface.params_formats import priceHistoryFormat
sys.path.append('../../')
from util.time_utils import date_now_str, posix_now, to_posix, posix_to_datestr
from util.crud_pg import crud
from util.postgres.db.models.tickers import Technicals as Technicals
from util.postgres.db.models.tickers import Symbols as Symbols


import pdb
import asyncio
import pandas as pd

tech = technicals()
db = crud()

async def query_and_load(ticker: str, posix_start_ms: int, posix_end_ms: int, query_only: bool = False):
    if posix_start_ms > posix_end_ms:
        print(f'Warning in {__file__}:\nStart date cannot occur before end date.')
        return

    price_history_query = {
        'symbol': ticker,
        'periodType': 'day',
        'period': '10',
        'frequency': '1',
        'frequencyType': 'minute',
        'startDate': posix_start_ms,
        'endDate': posix_end_ms,
        'needExtendedHoursData': 'true',
        'needPreviousClose': 'false'
    }

    price_history = tech.get_price_history(
        price_query=priceHistoryFormat(**price_history_query)
    )
    
    if price_history['empty']:
        print(f"Nothing returned for ticker -{ticker}-")
        return
    
    if query_only:
        return price_history
    else:
        candles = pd.DataFrame(price_history['candles'])
        tickercol = pd.DataFrame([ticker] * len(candles), columns=['ticker'])
        data = pd.concat([tickercol, candles], axis=1)
        data['datetime'] = data['datetime'] / 1000
        data = data.to_dict(orient='records')

        await db.insert_rows_orm(tablename=Technicals, 
                           index_elements=['ticker', 'datetime'], 
                           data=data)
    return

async def load_all_since(ticker, posix_date_sec):
    posix_now_sec = posix_now()
    # Since we can't query for long windows of time at 1minute frequencies,
    #   we break window down into 2 week blocks.
    
    window_span = posix_now_sec - posix_date_sec
    seconds_per_week = 60 * 60 * 24 * 7

    if window_span < ( seconds_per_week ):
        query_date_list = [posix_date_sec]
    else:
        ndates = int(window_span/( seconds_per_week ))
        stepsize = int(window_span/ndates)
        query_date_list = [val for val in range(posix_date_sec, posix_now_sec+1, stepsize)]
     
    # get data from each increment of date_list_posix
    query_date_list.append(posix_now_sec)

    for cnt, _ in enumerate(query_date_list[:-1]):
        await query_and_load(ticker, 
                       query_date_list[cnt]*1000, 
                       query_date_list[cnt+1]*1000)

    return

async def main():
    # Get List of all tickers   
    base_tickers = await db.query_table(Symbols, return_cols='ticker', unique_column_values='ticker')
    
    # Get posixtime of latest market day open
    found_latest_market_open_date = False
    check_posix_time_s = posix_now() - (60 * 60 * 24)
    while not found_latest_market_open_date:
        hours = tech.market_hours(posix_to_datestr(check_posix_time_s,'%Y-%m-%d'))
        if hours['equity'].get('EQ', None):
            
            if hours['equity']['EQ']['isOpen']:
                found_latest_market_open_date = True

        check_posix_time_s = check_posix_time_s - (60 * 60 * 24)
    
    latest_market_open = hours['equity']['EQ']['sessionHours']['regularMarket'][0]['start']
    latest_market_open = latest_market_open[:latest_market_open.rfind(':')] + '00'
    latest_market_open_posix = to_posix(latest_market_open, '%Y-%m-%dT%H:%M:%S%z')

    # Get relevant time window for all technicals collection
    relevant_window_start = to_posix('2025-01-01', '%Y-%m-%d')
    
    # Query table for all rows with datetime values greater than 
        # latest day market open posix, get unique tickers from that list
    up_to_date_tickers = await db.query_table(
            Technicals,
            return_cols='ticker',
            query_col='datetime', 
            query_val=latest_market_open_posix, 
            query_operation='gt',
            unique_column_values='ticker')

    if up_to_date_tickers:
        stale_tickers = [val for val in base_tickers if val not in up_to_date_tickers]
    else:
        stale_tickers = base_tickers

    # For each ticker
    for ticker in stale_tickers:
        # Get latest datetime
        # TODO in the future, use select distinct on tickers 
        #   order by datetime DESC limit 1 to query the db once for latest update time
        ticker_data = await db.query_table(
            Technicals,
            query_col='ticker', 
            query_val=ticker,
            unique_column_values='ticker')

        if ticker_data:
            latest_date = max([val[-1] for val in ticker_data])
        else:
            latest_date = relevant_window_start
        # load all data since latest datetime

        await load_all_since(ticker, latest_date)

if __name__ == "__main__":
    asyncio.run(main())