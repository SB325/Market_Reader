import uvicorn
from fastapi import FastAPI #, Body, Request
from fastapi.responses import JSONResponse
from webhook_response_model import webhook_response
import json
import pdb
import csv
import pprint
from datetime import datetime
from pytz import timezone
from push_notify import push_notify
tz = timezone('US/Eastern')

recent_tickers = {'records': {}}  # {"<ticker>", current_time}
recent_lookback_m = 30

app: FastAPI = FastAPI(root_path="/bzwebhook")
pn = push_notify()
to_pop = ['body','id','revision_id','type',
        'updated_at','authors','teaser',
        'tags','channels', 'url', 'created_at']

caplimit = 500_000_000
with open('nasdaq_screener.csv', 'r') as file:
    reader = csv.DictReader(file)
    bigticknas = []
    for row in reader:
        if float(row['Market Cap']) > caplimit:
            bigticknas.append(row['Symbol'])

with open('nyse_screener.csv', 'r') as file:
    reader = csv.DictReader(file)
    bigtickny = []
    for row in reader:
        if float(row['Market Cap']) > caplimit:
            bigtickny.append(row['Symbol'])

with open('amex_screener.csv', 'r') as file:
    reader = csv.DictReader(file)
    bigtickam = []
    for row in reader:
        if float(row['Market Cap']) > caplimit:
            bigtickam.append(row['Symbol'])

print(f"Number of Tickers with MCap > {caplimit}:")
print(f"{len(bigtickny) + len(bigticknas) + len(bigtickam)}")

with open('omit_words.json', 'r') as f:
    omit_words_dict = json.load(f)
    omit_words_dict = list(omit_words_dict.keys())

with open('good_words.json', 'r') as f:
    good_word_list = json.load(f)

def has_good_words(title: str):
    for word in good_word_list:
        if word.lower() in title.lower():
            return True, word.lower()
    return False, None

def has_omit_words(title: str):
    for word in omit_words_dict:
        if word.lower() in title.lower():
            return True, word.lower()
    return False, None

def has_omit_ticker(ticker: str):
    for tick in ticker:
        if tick in bigticknas or \
            tick in bigtickam or \
            tick in bigtickny or \
            '$' in tick:
            return True
    return False

def get_links(ticker_list: list):
    links = [f"<a href=\"https://finance.yahoo.com/quote/{tick}/\">{tick}</a>" for tick in ticker_list]
    secstr = '<br/>' + ''.join([f"{link}, " for link in links])
    return secstr

def has_recent_tickers(current_time, ticker_list, latency_m = 10):
    if recent_tickers['records']:
        items = []
        # remove old tickers from list
        for val in recent_tickers['records'].items():
            latency = (current_time - val[1]).seconds
            if latency < recent_lookback_m*60:
                # outside of lookback. keep item
                items.append(val)
        recent_tickers['records'] = dict(items)
         
        if items:
            for tick in ticker_list:
                if tick in recent_tickers['records'].keys():
                    since = (current_time - recent_tickers['records'][tick]).seconds
                    if since < latency_m*60:
                        return True, len(recent_tickers['records'])
    for tick in ticker_list:
        recent_tickers['records'].update({tick: current_time})
    return False, len(recent_tickers['records'])


@app.post("/")
async def root(data: webhook_response):
    response = JSONResponse(status_code=200, content="OK")
    try:
        current_time = datetime.now(tz)
        print(f'\nMessage Arrived at {current_time}.')
        data = data.model_dump()
        if data.get('data', None):
            content = data['data'].get('content', None)
            if content:
                securities = content.get('securities', None)
                if securities:
                    if len(securities)<=3:
                        author = content.get('authors', None)
                        if author:
                            if 'Benzinga Insights' not in author:
                                content['securities'] = [sym['symbol'] for sym in content['securities']] 
                                if not has_omit_ticker(content['securities']):
                                    title = content.get('title', None)
                                    if title:
                                        omitted, word = has_omit_words(title)
                                        if not omitted:
                                            hastick, lentick = has_recent_tickers(current_time, content['securities'])
                                            if not hastick:
                                                for p in to_pop:
                                                    content.pop(p)

                                                secstr = get_links(content['securities'])    
                                                if has_good_words(title):
                                                    title = '***' + title
                                                pprint.pp(content)
                                                _ = pn.send(title='News',
                                                            message=f"<b>{title}</b>\n{secstr[:-2]}",
                                                            html = 1
                                                            )
                                            else:
                                                print(f"Omitted Repeated Ticker {content['securities']} from recent list {lentick} long.")
                                        else:
                                            print(f"Title has an Omit word [{word}] for ticker {content['securities']}.")
                                    else:
                                        print('No title field found.')
                                else:
                                    print(f"Omit Ticker Found {content['securities']}.")
                            else:
                                print('Benzinga Insights author omitted.')
                        else:
                            print("No author field found.")
                    else:
                        print('Securities list too long.')
                else:
                    print('Securities Field not present.')
            else:
                print('Content Field not present.')
        else:
            print('Data Field not present.')
    
    except:
      
        return JSONResponse(status_code=204, content="NoContent")
    return response

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8001, reload=True)
