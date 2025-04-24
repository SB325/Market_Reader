import pdb
import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from pipelines.press_releases.newswires import newswire
from util.elastic.crud_elastic import crud_elastic
from util.crud_pg import crud
from util.postgres.db.models.tickers import Technicals
from util.time_utils import to_posix, minute_of_day, day_of_week
from pipelines.press_releases.newswire_client import get_tickers
import pandas as pd
from models.embeddings import group_similar_documents, return_documents_in_group, embeddings
from labeled_data import labeleddata
import asyncio
from tqdm import tqdm
import asyncio
import csv
import numpy as np
from keras import models, Input
from keras.layers import Dense, Normalization
import pickle
import tensorflow as tf

elastic = crud_elastic()
nw = newswire(elastic)
pg = crud()

from_pkl = True

pd.set_option('display.max_colwidth', 300)

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

# Add column for 
    # - time of day (seconds since 12:00AM that day)
    # - day of week

def get_minute_of_day(news_time_s: int = 1740066998):
    return minute_of_day(news_time_s)

def get_day_of_week(news_time_s: int = 1740066998):
    # Return the day of the week as an integer, where Monday is 0 and Sunday is 6
    return day_of_week(news_time_s)

def get_cum_volume_pre_news(symbol: str = 'TSLA', news_time_s: list[int] = [1740066998]):
    
    hour_before_news = [time_ - 3600 for time_ in news_time_s]
    five_min_before_news = [time_ - (60 * 5) for time_ in news_time_s]
    
    symbol_volumes = asyncio.run(pg.query_table(Technicals, 
                                                return_cols=['datetime', 
                                                             'volume'],
                                                query_col='ticker',
                                                query_val=symbol,
                                                sort_column = 'datetime',
                                                sort_order = 'desc'
                                                )
    )
    
    if symbol_volumes:
        volume_data = pd.DataFrame(symbol_volumes, columns=['posixtime','volume'])
    
    volume_trend_ratio = []
    for ind, hour_before in enumerate(hour_before_news):
        volume_hour_pre = volume_data.volume[
            (volume_data.posixtime > hour_before) & 
            (volume_data.posixtime <= news_time_s[ind])
            ].median()
        volume_minutes_pre = volume_data.volume[
            (volume_data.posixtime > five_min_before_news[ind]) & 
            (volume_data.posixtime <= news_time_s[ind])
            ].median()
    
        if volume_hour_pre == 0:
            ratio = np.nan
        else:
            ratio = volume_minutes_pre/volume_hour_pre
        volume_trend_ratio.append(ratio)
        
    return volume_trend_ratio

def get_minute_of_day(news_time_s: int):
    return minute_of_day(news_time_s)

def get_day_of_week(news_time_s: list[int] = [1740066998]):
    return [day_of_week(time_) for time_ in news_time_s]

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
                                        conditional='eq',
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
                                                    threshold=0.5)
                if value:
                    features.append(value)
            
            feature_df = pd.DataFrame(features, 
                                    columns=['max_gain_24','day_gain_24','max_loss_24']
                        )
            volume_trend = get_cum_volume_pre_news(ticker, [int(date_/1000) for date_ in articles_df.created])
            day_of_wk = get_day_of_week([int(date_/1000) for date_ in articles_df.created])
            volume_trend_df = pd.DataFrame(volume_trend, columns=['volume_trend'])
            day_of_wk_df = pd.DataFrame(day_of_wk, columns=['day_of_week'])
            
            model_input.append(pd.concat([
                                articles_df, 
                                feature_df, 
                                volume_trend_df,
                                day_of_wk_df
                                ], 
                                axis=1))
    
        full_model_df = pd.concat(model_input)
        full_model_df['title'] = full_model_df['title'].fillna('')
        full_model_df['ticker'] = full_model_df['ticker'].fillna('')

        # Add marketCap data to full_model_df
        full_model_df = pd.merge(full_model_df, securities_df, left_on='ticker', right_on='symbol', how='left').drop('symbol', axis=1)
        full_model_df.dropna(subset='id', inplace=True)

        ldata = labeleddata(full_model_df)
        ldata.save_data()

    if from_pkl:
        ldata = labeleddata()
        ldata.load_data()
    
    # Now build model from labeleddata object
    training_set, testing_set = ldata.train_test_split(0.8)
    
    use_pickle_training = True
    
    emb = embeddings()
    if use_pickle_training:
        with open('training_data.pkl', 'rb') as pickle_file:
            inputdata = pickle.load(pickle_file)
    else:
        inputdata = dict.fromkeys(['train_x','train_y','test_x','test_y'])
        inputdata['train_x'] = emb.encode(training_set.title.tolist())
        inputdata['train_y'] = np.array(training_set.day_gain_24.tolist()).astype("int32")
        inputdata['test_x'] = emb.encode(testing_set.title.tolist())
        inputdata['test_y'] = np.array(testing_set.day_gain_24.tolist()).astype("int32")
        with open('training_data.pkl', "wb") as file:
            pickle.dump(inputdata, file)

    # https://stackoverflow.com/questions/37232782/nan-loss-when-training-regression-network
    
    # Input - Layer
    inputdata['train_y'] = inputdata['train_y'].astype("int32")
    inputdata['test_y'] = inputdata['test_y'].astype("int32")
    
    training_shape = inputdata['train_x'].shape
    test_shape = inputdata['train_y'].shape
    training_samples = training_shape[0]
    features = training_shape[1]
    test_samples = test_shape[0]

    batch_size_ = 1000
    epochs = 100
    
    model = models.Sequential()

    # For this data, the each data is the vector of length(features), and number of samples = len(training_samples)
    # Therefore, shape is (features,) which accounts for a single sample
    model.add(
        Input(
            shape=(features,),
            batch_size=batch_size_,
            dtype="float32",
            sparse=None,
            ragged=None,
            batch_shape=None,
            name="Input Layer",
            optional=False
        )
    )
    # model.add(layers.LSTM(units=2,
    #                       recurrent_dropout=0
    #                       )
    #             )
    model.add(Dense(units=1, activation='sigmoid', input_shape=(training_samples,features,)))

    model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"]
            )
    
    """
    Epoch 100/100
    31/31 - 0s - 3ms/step - accuracy: 0.0023 - loss: nan - val_accuracy: 0.0024 - val_loss: nan
    """
    layer = Normalization(axis=-1)
    layer.adapt(inputdata['train_x'])   
    results = model.fit(
                x=layer(inputdata['train_x']), 
                y=inputdata['train_y'],
                batch_size=batch_size_,
                epochs=epochs,
                validation_data=(layer(inputdata['test_x']), inputdata['test_y']),
                verbose=2
            )
    
    scores = model.evaluate(inputdata['test_x'], inputdata['test_y'], verbose=0)
    print("Accuracy: %.2f%%" % (scores[1]*100))

    pdb.set_trace()

