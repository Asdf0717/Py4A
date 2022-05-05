import json
import requests
from datetime import datetime
import dateutil.relativedelta
import os 

mr_username = ''
mr_pass = ''
api_url = 'https://www.muckrock.com/api_v1/'


response = requests.post('https://www.muckrock.com/api_v1/token-auth/', data={'username': mr_username, 'password': mr_pass})
data = response.json()
token = data['token']
print('Token received from MR successfully')


def get_headers(token=None):
    if token:
        return {
        'Authorization': 'Token %s' %token,
        'content-type': 'application/json'
        }
    else:
        return {'content-type': 'application/json'}


# first get today's month then subtract one month to grab previous
s = str(datetime.now())[0:10]
d = datetime.strptime(s, "%Y-%m-%d")
d2 = d - dateutil.relativedelta.relativedelta(months=1)
d2 = str(d2)[0:7]


foia_doc = json.dumps({
    'jurisdiction': 169,
    'agency': 503,
    'title': 'Last Month\'s 1505 checks',
    'document_request': 'For the year and month of ' + d2 + ', I am requesting a list of all 1505 checks expenditures issues by the Bureau of Organized Crime. I am requesting the full list of checks spent by the BoC during the full month of ' + d2 + '. ',
    })

head = get_headers(token)
print(head)
print(type(head))


foia_url=api_url+'foia/'

r = requests.post(foia_url, data=foia_doc, headers=head)
print(r.text)
print(r.status_code)
