import pdb
import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from pipelines.press_releases.newswires import newswire
from util.elastic.crud_elastic import crud_elastic
from util.crud_pg import crud
from util.postgres.db.models.tickers import Technicals
import pandas as pd
import asyncio

elastic = crud_elastic()
nw = newswire(elastic)
pg = crud()

def fewer_ticker_symbols(ticker, symbol_list: list):
    symbols = [symbol['name'] for symbol in symbol_list]
    return (ticker in symbols) and (len(symbols) <= 3)

def get_price_features_from_news(created_date, technicals: pd.DataFrame, range_s):
    tech_filtered = technicals[(technicals['datetime'] >= created_date-range_s) &
               (technicals['datetime'] <= created_date+range_s)]
    pdb.set_trace()
    value = []
    return value

if __name__ == "__main__":
    ticker = 'AAPL'
    date_range_s = 3600*24
    response = nw.search_ticker(index=nw.index, ticker=ticker)
    articles = [val['_source'] for val in response['hits']['hits'] \
                if fewer_ticker_symbols(ticker, val['_source']['stocks'])]
    articles_df = pd.DataFrame(articles)

    articles_df.drop(['updated', 'channels', 'stocks', 'tags'], 
                    axis=1, 
                    inplace=True
                    )

    columns = ['ticker',
                'open',
                'high',
                'low',
                'close',
                'volume',
                'datetime'
    ]
    base_tickers = asyncio.run(pg.query_table(Technicals, 
                                        return_cols=columns,
                                        query_col='ticker',
                                        query_val=ticker
                                        )
    )
    technicals_df = pd.DataFrame(base_tickers, columns=columns)

    features = []
    for date_ in articles_df.created:
        features.append(get_price_features_from_news(int(date_/1000), 
                                               technicals_df, 
                                               date_range_s))
pdb.set_trace()


# For each news entry, get time of entry and use schwab api to get the 24hrs prior and after