# -*- coding: utf8 -*-

import json
import urllib2
import urllib
import sys
import os
from argparse import ArgumentParser
from collections import defaultdict

def log(message):
    sys.stdout.write(message + os.linesep)

class TodoistAPI(object):
    def __init__(self, email, password):
        self.token = self._api_call('login', {'email': email, 'password': password}, add_token=False)['token']

    def _api_call(self, api_method, parameters, add_token=True):
        parameters = dict(parameters)
        if add_token:
            parameters.update({'token': self.token})
        params = urllib.urlencode(parameters)
        url = u'https://todoist.com/API/%s?%s' % (api_method, params)
        log('Calling url %s' % url)
        return_value = json.load(urllib2.urlopen(url))
        if type(return_value) is unicode:
            raise Exception('Call finished with error! %s' % return_value)
        return return_value

    def add_list(self, list_name):
        log('Adding list %s' % list_name)
        return self._api_call('addProject', {'name': list_name})['id']

    def add_task(self, list_id, task_name):
        log('Adding task %s to list %d' % (task_name, list_id))
        return self._api_call('addItem', {'project_id': list_id, 'content': task_name})['id']


def create_parser():
    parser = ArgumentParser()
    parser.add_argument('wunderlist_dump_json')
    parser.add_argument('todoist_email')
    parser.add_argument('todoist_password')
    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    todoist_api = TodoistAPI(args.todoist_email, args.todoist_password)

    with open(args.wunderlist_dump_json) as f:
        j = json.load(f)
        lists = {}
        for l in j['lists']:
            lists[l['id']] = todoist_api.add_list(l['title'])
        lists['inbox'] = todoist_api.add_list('inbox')
        for t in j['tasks']:
            todoist_api.add_task(lists[t['list_id']], t['title'])