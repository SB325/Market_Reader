from newswires import newswire
import pdb
import json

nw = newswire()

params = {'displayOutput': 'full',
          'tickers': 'HUSA',
          'sort': 'created:desc',
          'dateFrom': '2024-12-11'}
news_history = nw.get_news_history(params = params)
print(news_history)

