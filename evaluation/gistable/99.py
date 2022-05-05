# v1.0 of a command line uploader for the koken gallery software.
# The only non-standard requirement is pyton-requests.

import json
import requests
import os
from urllib import quote as quote

api_url = "http://yourdomain/api.php?"
common_headers = {'X-Koken-Auth':'cookie'}
email = quote('your@email.com')
password = quote('YourPassword')

# Establish an authenticated session
auth = requests.Session()
auth.post(api_url + '/sessions',
    data={'email': email, 'password': password},
    headers=common_headers)

def create_album(title):
    res = auth.post(api_url + '/albums',
        data={'title': title, 'album_type': '0', 'listed': '1'},
        headers=common_headers)
    id = res.json['id']
    log('Created album: %s, id: %s' % (title, id))
    return(id)

def upload_localfile(file):
    res = auth.post(api_url + '/content',
        data={'localfile': file, 'visibility': 'public'},
        headers=common_headers)
    id = res.json['id']
    log('Uploaded localfile %s, id: %s' % (file, id))
    return(id)

def add_content_to_album(content_id, album_id):
    res = auth.post(api_url + '/albums/%s/content/%s' % (album_id, content_id),
        data={'localfile': file, 'visibility': 'public'},
        headers=common_headers)
    log('Added %s to album %s' % (content_id, album_id))
    return

def log(msg):
    print(msg)


# Create an album named the same as your current working directory,
# and upload each file within to the new album.
cwd = os.getcwd()
dname = cwd.split('/')[-1]
album_id = create_album(dname)

for file in os.listdir(cwd):
    content_id = upload_localfile(cwd + '/' + file)
    add_content_to_album(content_id, album_id)