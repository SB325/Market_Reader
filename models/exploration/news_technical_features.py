import pdb
import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from pipelines.press_releases.newswires import newswire
from util.elastic.crud_elastic import crud_elastic
from util.crud_pg import crud
from util.postgres.db.models.tickers import Technicals
from util.time_utils import to_posix
from pipelines.press_releases.newswire_client import get_tickers
import pandas as pd
from models.embeddings import group_similar_documents, return_documents_in_group
from labeled_data import labeleddata
import asyncio
from tqdm import tqdm
import asyncio
import csv
import numpy as np
from keras.utils import to_categorical
from keras import models
from keras import layers

elastic = crud_elastic()
nw = newswire(elastic)
pg = crud()

pd.set_option('display.max_colwidth', 100)

def assign_output_value(value, threshold):
    # above +threshold = 2
    # between +/- threshold = 1
    # below -threshold = 0
    val =  2 if (value > threshold) else \
            0 if (value < -threshold) else \
            1
    return val

def fewer_ticker_symbols(ticker, symbol_list: list):
    symbols = [symbol['name'] for symbol in symbol_list]
    return (ticker in symbols) and (len(symbols) <= 3)

def get_price_features_from_news(created_date, 
                                 technicals: pd.DataFrame, 
                                 range_s: int = 0,
                                 threshold: int = 0):
    fail_value = [-1, -1, -1]
    tech_filtered = technicals[(technicals['datetime'] > (created_date + 60)) &
               (technicals['datetime'] <= (created_date+range_s))]
    
    # Create a feature candle where 
    # open is the minute candle right after created_date
    if tech_filtered.empty:
        return fail_value
    if (int(tech_filtered.iloc[-1].datetime) - created_date) > (60*20):
        # Too much time has passed after news before next active candle
        return fail_value
    
    feat_price_open = float(tech_filtered.iloc[-1].open)
    if not feat_price_open:
        return fail_value
    # high is the greatest high value within 24 hours after created_date
    feat_price_high = float(tech_filtered.high.max())
    # low is the least low value withing 234 hours after created_date
    feat_price_low = float(tech_filtered.low.min())
    # close is the first close value before 24 hours post created_date
    feat_price_close = float(tech_filtered.iloc[0].close)
    
    feature_max_gain_24_hrs = (feat_price_high-feat_price_open)/feat_price_open
    feature_day_gain_24_hrs = (feat_price_close-feat_price_open)/feat_price_open
    feature_max_loss_24_hrs = (feat_price_low-feat_price_open)/feat_price_open

    value = [ assign_output_value(feature_max_gain_24_hrs, threshold),
            assign_output_value(feature_day_gain_24_hrs, threshold),
            assign_output_value(feature_max_loss_24_hrs, threshold)
    ]

    return value

securities = []
with open('nasdaq_screener.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if not row['Market Cap']:
            row['Market Cap'] = -1
        securities.append({
                'symbol': row['Symbol'],
                'market_cap': int(float(row['Market Cap'])),
                'country': row['Country'],
                'sector': row['Sector'],
                'industry': row['Industry']
        })
securities_df = pd.DataFrame.from_dict(securities)

if __name__ == "__main__":
    model_input = []
    tickers = asyncio.run(get_tickers())
    
    from_pkl = True
    if not from_pkl:
        for ticker in tqdm(tickers):
            date_range_s = 3600*24
            
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
                                                query_val=ticker,
                                                sort_column = 'datetime',
                                                sort_order = 'desc'
                                                )
            )
            
            if not base_tickers:
                continue
            technicals_df = pd.DataFrame(base_tickers, columns=columns)

            desired_first_time = to_posix(
                    "01/08/2025 12:00 AM", dateformat_str = "%m/%d/%Y %I:%M %p"
                    )*1000
            desired_last_time = (base_tickers[0][-1] - 3600 * 24 ) *1000 

            # Elasticsearch contains duplicate entries! TODO: Remove/Avoid
            # in next update!!
            # https://discuss.elastic.co/t/avoid-duplicate-insertions/374809/2
            response = nw.search_ticker(index=nw.index, 
                                        ticker=ticker,
                                        query_on_key = 'created',
                                        query_on_val = [desired_first_time,desired_last_time]
                                        )
            
            articles = [val['_source'] for val in response['hits']['hits'] \
                        if fewer_ticker_symbols(ticker, val['_source']['stocks']) ] # and
                        #val['_source']['created']==val['_source']['updated']]
            
            if not articles:
                continue

            articles_df = pd.DataFrame(articles)
            
            articles_df.drop(['updated', 'channels', 'stocks', 'tags'], 
                            axis=1, 
                            inplace=True
                            )
            articles_df.drop_duplicates(subset=['id'], inplace=True)
            
            features = []
            for date_ in articles_df.created:
                value = get_price_features_from_news(int(date_/1000), 
                                                    technicals_df, 
                                                    range_s=date_range_s,
                                                    threshold=0.2)
                if value:
                    features.append(value)
            
            feature_df = pd.DataFrame(features, 
                                    columns=['max_gain_24','day_gain_24','max_loss_24']
                        )
            model_input.append(pd.concat([articles_df, feature_df], axis=1))
    
        full_model_df = pd.concat(model_input)
        full_model_df['title'] = full_model_df['title'].fillna('')
        full_model_df['ticker'] = full_model_df['ticker'].fillna('')

        # Add marketCap data to full_model_df
        full_model_df = full_model_df.merge(full_model_df, securities_df, left_on='ticker', right_on='symbol', how='left').drop('symbol', axis=1)
        ldata = labeleddata(full_model_df)
        ldata.save_data()
        # full_model_df.to_pickle('full_model_df.pkl')

    if from_pkl:
        ldata = labeleddata()
        ldata.load_data()
    
    # Now build model from labeleddata object
    ldata.train_test_split()
    pdb.set_trace()

