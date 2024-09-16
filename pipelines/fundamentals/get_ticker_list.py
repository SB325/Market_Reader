'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import requests
import pdb
import json

url='https://www.sec.gov/files/company_tickers.json'
# url_in = 'https://www.sec.gov/Archives/edgar/cik-lookup-data.txt'
header = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}

output_filename = 'tickers.json'

response = requests.get(url=url, headers=header)
# pdb.set_trace()

with open(output_filename,'w') as file:
    file.write(json.dumps(response.json()))

