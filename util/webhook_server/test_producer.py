import requests
import json

dict_ = {'id': '08b7022d-78db-4d44-90c6-8601f4087d2c', 'api_version': 'webhook/v1', 'kind': 'News/v1', 'data': {'action': 'Created', 'id': 1234567890, 'content': {'id': 0, 'revision_id': 0, 'type': 'story', 'created_at': '2025-01-14T06:21:54.425573986Z', 'updated_at': '2025-01-14T06:21:54.425574157Z', 'title': 'Company A reports record earnings in Q1', 'body': 'During a Pre-Market earnings announcement Company A reported ...', 'authors': ['Scott Rubin'], 'teaser': 'During a Pre-Market earnings announcement ...', 'url': '', 'tags': ['Earnings'], 'securities': [{'symbol': 'GOOG', 'exchange': 'NASDAQ', 'primary': False}], 'channels': ['News', 'Movers & Shakers']}, 'timestamp': '2025-01-15T02:22:06.542868447Z'}}
jsonstr = json.dumps(dict_)
print(jsonstr)
# url_in = "http://crunchy.dyndns.org/test/test_endpoint"
# headers = {'Content-Type': 'application/json'}
# json_in = {"hi": "there$"}
# response = requests.post(url=url_in, json=json_in, headers=headers)