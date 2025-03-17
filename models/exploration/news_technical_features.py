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
import asyncio
from tqdm import tqdm
import asyncio
import csv

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

caplimit = 200_000
with open('nasdaq_screener.csv', 'r') as file:
    reader = csv.DictReader(file)
    bigticknas = []
    for row in reader:
        mktcap = row['Market Cap']
        if mktcap:
            if float(mktcap) > caplimit:
                bigticknas.append(row['Symbol'])

print(f"Number of Tickers with MCap > {caplimit}:")
print(f"{len(bigticknas)}")

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
        full_model_df.to_pickle('full_model_df.pkl')

    if from_pkl:
        full_model_df = pd.read_pickle('full_model_df.pkl')
        pos24_stats = pd.read_pickle('pos24_stats.pkl')
        neu24_stats = pd.read_pickle('neu24_stats.pkl')
        neg24_stats = pd.read_pickle('neg24_stats.pkl')
    else:
        N_max_gain = len(full_model_df.max_gain_24[full_model_df.max_gain_24==2])
        N_day_gain = len(full_model_df.day_gain_24[full_model_df.day_gain_24==2])
        N_max_loss = len(full_model_df.max_loss_24[full_model_df.max_loss_24==2])
        print(f"N_max_gain: {N_max_gain}")
        print(f"N_day_gain: {N_day_gain}")
        print(f"N_max_loss: {N_max_loss}")
        pos24 = full_model_df[full_model_df['day_gain_24']==2]
        neu24 = full_model_df[full_model_df['day_gain_24']==1]
        neg24 = full_model_df[full_model_df['day_gain_24']==0]
        
        thresh = 0.8
        pos24_stats = group_similar_documents(pos24['title'].tolist(), thresh=thresh)
        neu24_stats = group_similar_documents(neu24['title'].tolist(), thresh=thresh)
        neg24_stats = group_similar_documents(neg24['title'].tolist(), thresh=thresh)
        pos24_docs = return_documents_in_group(pos24_stats['corpus'], pos24_stats['ngroups']-1)
        neu24_docs = return_documents_in_group(neu24_stats['corpus'], neu24_stats['ngroups']-1)
        neg24_docs = return_documents_in_group(neg24_stats['corpus'], neg24_stats['ngroups']-1)
        pos24_stats['corpus'].to_pickle('pos24_stats.pkl')
        neu24_stats['corpus'].to_pickle('neu24_stats.pkl')
        neg24_stats['corpus'].to_pickle('neg24_stats.pkl')
    pdb.set_trace()
    cheap_stock = full_model_df[~full_model_df['ticker'].str.contains("|".join(bigticknas))]
    N_max_gain = len(cheap_stock.max_gain_24[cheap_stock.max_gain_24==2])
    N_day_gain = len(cheap_stock.day_gain_24[cheap_stock.day_gain_24==2])
    N_max_loss = len(cheap_stock.max_loss_24[cheap_stock.max_loss_24==2])

    pos24 = cheap_stock[cheap_stock['day_gain_24']==2]
    neu24 = cheap_stock[cheap_stock['day_gain_24']==1]
    neg24 = cheap_stock[cheap_stock['day_gain_24']==0]
    
# For each news entry, get time of entry and use schwab api to get the 24hrs prior and after