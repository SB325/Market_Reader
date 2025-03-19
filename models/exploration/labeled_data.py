import pandas as pd
from enum import Enum
import numpy as np
import pdb

class Label(Enum):
    positive = 2
    neutral = 1
    negative = 0
    na = None

class labeleddata():
    labels : Label = None
    fulldata: pd.DataFrame
    model_data: dict = {}
    def __init__(self, fulldata: pd.DataFrame = None):
        if fulldata:
            self.parse_data(fulldata)

    def parse_data(self, fulldata):
        self.fulldata = fulldata
        self.model_data['24hours'] = {
            'data': {
            'positive': fulldata[fulldata['day_gain_24']==2],
            'neutral': fulldata[fulldata['day_gain_24']==1],
            'negative': fulldata[fulldata['day_gain_24']==0]
            },
            'summary': {
                'Npositive': len(fulldata[fulldata['day_gain_24']==2]),
                'Nneutral': len(fulldata[fulldata['day_gain_24']==1]),
                'Nnegative': len(fulldata[fulldata['day_gain_24']==0])
            }
        }
        self.model_data['max24hours'] = {
            'data': {
                'positive': fulldata[fulldata['max_gain_24']==2],
                'neutral': fulldata[fulldata['max_gain_24']==1],
                'negative': fulldata[fulldata['max_gain_24']==0]
            }, 
            'summary': {
                'Npositive': len(fulldata[fulldata['max_gain_24']==2]),
                'Nneutral': len(fulldata[fulldata['max_gain_24']==1]),
                'Nnegative': len(fulldata[fulldata['max_gain_24']==0])
            }
        }
        self.model_data['min24hours'] = {
            'data': {
                'positive': fulldata[fulldata['max_loss_24']==2],
                'neutral': fulldata[fulldata['max_loss_24']==1],
                'negative': fulldata[fulldata['max_loss_24']==0]
            },
            'summary': {
                'Npositive': len(fulldata[fulldata['max_loss_24']==2]),
                'Nneutral': len(fulldata[fulldata['max_loss_24']==1]),
                'Nnegative': len(fulldata[fulldata['max_loss_24']==0])
            }
        }

    def print_histogram(self, series, bins=10):
        """Prints a text-based histogram of a Pandas Series to the terminal."""

        counts, bin_edges = np.histogram(series, bins=bins)
        max_count = counts.max()
        
        for i in range(bins):
            bar = '#' * int(counts[i] / max_count * 20) # Scale bar length for terminal width
            print(f'{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}: {bar} ({counts[i]}: {100*counts[i]/sum(counts)}%)')

    def save_data(self, filename: str = 'full_model_df.pkl'):
        self.fulldata.to_pickle(filename)

    def load_data(self, filename: str = 'full_model_df.pkl'):
        self.fulldata = pd.read_pickle(filename)
        self.parse_data(self.fulldata)

    def train_test_split(self):
        # Get list of unique tickers in alphabetical order
        ticker_sorted = self.fulldata.ticker.dropna().sort_values().unique()
        ind = np.arange(len(ticker_sorted))
        np.random.shuffle(ind)
        split_index = int(0.8 * len(ind))
        train_index, test_index = np.split(ind, [split_index])
        pdb.set_trace()
        training_set = self.fulldata[self.fulldata.ticker==ticker_sorted[train_index]]
        testing_set = self.fulldata[self.fulldata.ticker==ticker_sorted[test_index]]
        return training_set, testing_set
## NOTE ##
# 90+ percent of positive and negative 24 hour price action after a news headline occurs
# for market_cap < 10B, with vast majority of those occurring for 
# <2B market_caps
#
