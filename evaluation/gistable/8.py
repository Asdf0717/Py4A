#!/usr/bin/env python
""" Sends Jenkins build duration statistics to Graphite. """
import requests
import json
from graphite import Graphite # This is our closed-source library but you get the idea.

JENKINS_URL='http://jenkins'
GRAPHITE_HOST='10.x.x.x'
GRAPHITE_PREFIX='jenkins.main.build_time.'

def get_jobs(host):
    response = json.loads(requests.get('%s/api/json' % host).text)
    return response['jobs']

def get_build_details(job_url):
    return json.loads(requests.get('%s/lastSuccessfulBuild/api/json' % job_url).text)

if __name__ == '__main__':
    graphite = Graphite(GRAPHITE_HOST)

    for job in get_jobs(JENKINS_URL):
        build = get_build_details(job['url'])
        graphite.send_metric(GRAPHITE_PREFIX + job['name'],
                        int(build['duration']) // 1000,
                        int(build['timestamp']) // 1000)
