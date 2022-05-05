#!/usr/bin/env python3

import json
import time

import requests

from ntfy.backends.default import notify

USER = 'YOUR USERNAME'
TOKEN = 'YOUR TOKEN'
API_URL = 'https://api.github.com'


while time.sleep(30) or True:
    resp = requests.get(API_URL + '/notifications', auth=(USER, TOKEN),
                        verify=False)

    for notification in resp.json():
        notify(
            notification['repository']['full_name'],
            notification['subject']['title'],
            icon='/usr/share/icons/Numix-Circle/48x48/apps/gitg.svg',
        )
