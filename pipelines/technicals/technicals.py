#################################################
# Technicals ingest
#################################################
# This script pulls raw technical data from schwab
#   and ingests them into the database

from ameritrade_auth import schwab_auth
from params_formats import priceHistoryFormat
import sys
sys.path.append('../../')
from util.time_utils import to_posix, posix_now 
from enum import Enum
import pdb

class tech_ingest():    
    def __init__(self, auth: schwab_auth):
        self.auth = auth
        self.resource_url = 'https://api.schwabapi.com/marketdata/v1'

    def market_hours(self, date):
        '''
        Get Market Hours for dates in the future across different markets.
        Date cannot be more than 7 days in the past.
        Date format:YYYY-MM-DD
        '''
        
        querydate = to_posix(
            f"{date} 12:00 AM EST", dateformat_str = "%Y-%m-%d %I:%M %p %Z"
            )
        now = posix_now()

        span = now-querydate
        assert span < (3600 * 24 * 7), "Date cannot be more than 7 days in the past."

        data = self.auth.get_request(
                    url=f"{self.resource_url}/markets", 
                    params={'markets':'equity', 'date': date}
            )  

        if not data.ok:
            msg=f'{ __file__}: market_hours data call failed'
            print(msg)
        else:
            print(f"{__file__}: Downloaded Market Hours for {date}.")

        return data
    
    def get_price_history(self, price_query: priceHistoryFormat):
        # args are described in the priceHistoryFormat pydantic model
        # query ranges of no more than 10 business days.
        '''
            parameters: ... 
                when startDate set to a low time, candles are returned as far back as 
                ~28 days to yesterday when frequencyType is minute.
            returns: response object with json obj that has the following keys:
                candles[List[dict]], symbol [str], empty [bool]

                candles.keys() = ['open','high','low','close','volume','datetime']
                    where datetime is in milliseconds
        '''
        query = price_query.model_dump(exclude_none=True)
        query_ready = { k : (v.name if isinstance(v, Enum) else v) 
                       for k,v in query.items()}

        data = self.auth.get_request(
                    url=f"{self.resource_url}/pricehistory", 
                    params=query_ready
            )  

        if not data.ok:
            msg=f'{ __file__}: get_price_history data call failed'
            print(msg)
        else:
            print(f"{__file__}: Downloaded price history for {query_ready['symbol']}.")

        return data
            
    def get_quotes(self,tickers: list):        
        ticker_list_string = ','.join(tickers)
        data = self.auth.get_request(url=f'{self.resource_url}/quotes', 
            params={'symbols': ticker_list_string},
        )
        
        if not data.ok:
            msg=f'{ __file__}: get_quotes data call failed'
            print(msg)
        else:
            print([f'{ __file__}: Downloaded quotes for {ticker_list_string}.'])
        return data

    def get_quote(self,tick: str):
        # len(varargin) must be 2. varargin[0] is a ticker symbol        
        data = self.auth.get_request(url=f'{self.resource_url}/{tick}/quotes')
        
        if not data.ok:
            msg=f"{ __file__}: data request for get_quote" + \
            f"failed.({data.status_code}: Request {data.request})" + \
            f"Headers: {data.headers}"
            print(msg)
        else:
            print([f'{ __file__}: Downloaded quote for {tick}.'])
        return data

if __name__ == "__main__":
    auth = schwab_auth()
    ti = tech_ingest(auth)
    # response = ti.get_quotes(['TSLA','AA'])

    # price_history_query = {
    #     'symbol': 'TSLA',
    #     'periodType': 'day',
    #     'period': '10',
    #     'frequency': '1',
    #     'frequencyType': 'minute',
    #     'startDate': to_posix(
    #         "12/01/2024 12:00 AM EST", dateformat_str = "%m/%d/%Y %I:%M %p %Z"
    #         )*1000,
    #     'endDate': to_posix(
    #         "02/01/2025 12:00 AM EST", dateformat_str = "%m/%d/%Y %I:%M %p %Z"
    #         )*1000,
    #     'needExtendedHoursData': 'true',
    #     'needPreviousClose': 'true'
    #     }

    # val = ti.get_price_history(
    #             price_query=priceHistoryFormat(**price_history_query)
    #             )

    val = ti.market_hours(date='2025-02-18')
    print(val.json())
    pdb.set_trace()
