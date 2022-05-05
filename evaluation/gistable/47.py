#!/usr/bin/python

from __future__ import print_function
import urllib
import json
import sys
import base64

search    = urllib.quote(sys.argv[1])
json_data = urllib.urlopen("http://api.giphy.com/v1/gifs/search?q={searchterm}&api_key=dc6zaTOxFJmzC&limit=1".format(searchterm=search)).read()
data      = json.loads(json_data)
gif       = data["data"][0]["images"]["fixed_height"]["url"]
gif_data  = urllib.urlopen(gif).read()
print("\033]1337;File=inline=1:"+base64.b64encode(gif_data))
