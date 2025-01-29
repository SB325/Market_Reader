import requests
import json
import pdb

dict_ = {'id': 'f0fe9cca-f2d0-452f-adb6-77f7c18a98d9',
            'api_version': 'webhook/v1',
            'kind': 'News/v1',
            'data': {'action': 'Created',
                'id': 96995380,
                'content': {'id': 43221984,
                      'revision_id': 51522882,
                      'type': 'story',
                      'created_at': '2025-01-28T18:09:35Z',
                      'updated_at': '2025-01-28T18:09:36Z',
                      'title': 'Goldman Sachs Twilio to Buy, Raises '
                               'Price Targe to $185',
                      'authors': ['Benzinga Newsdesk'],
                      'teaser': 'Goldman Sachs Kash Rangan  '
                                'Twilio (NYSE:TWLO) from Neutral to Buy and '
                                'raises the price targe from $77 to $185.',
                      'url': 'https://www.benzinga.com/news/25/01/43221984/goldman-sachs-upgrades-twilio-to-buy-raises-price-target-to-185',
                      'tags': [],
                      'securities': [{'symbol': 'TWLD',
                                      'exchange': 'NYSE',
                                      'primary': True}],
                      'channels': ['News',
                                   'Upgrades',
                                   'Price Target',
                                   'Analyst Ratings']},
          'timestamp': '2025-01-28T18:39:09.035893652Z'}}

# pdb.set_trace()
#jsonstr = json.dumps(dict_)
# print(jsonstr)
url_in = "http://crunchy.dyndns.org/bzwebhook/"
headers = {'Content-Type': 'application/json'}
json_in = dict_
response = requests.post(url=url_in, json=json_in, headers=headers)
print(response.json())
