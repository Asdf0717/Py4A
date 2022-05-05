import requests
from requests.auth import OAuth1

url = u'https://api.twitter.com/1/account/settings.json'

client_key = u'...'
client_secret = u'...'
resource_owner_key = u'...'
resource_owner_secret = u'...'

queryoauth = OAuth1(client_key, client_secret,
                    resource_owner_key, resource_owner_secret,
                    signature_type='query')
headeroauth = OAuth1(client_key, client_secret,
                     resource_owner_key, resource_owner_secret,
                     signature_type='auth_header')
bodyoauth = OAuth1(client_key, client_secret,
                   resource_owner_key, resource_owner_secret,
                   signature_type='body')

r_query = requests.get(url, auth=queryoauth)
r_header = requests.get(url, auth=headeroauth)
r_body = requests.post(url, auth=bodyoauth)
