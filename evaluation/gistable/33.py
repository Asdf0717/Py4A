# reddit_test.py
import urllib.request
import json
from pdb import set_trace
from time import sleep, time

def timeit( func2wrap ):
    def wrapped_func(*args):
        start_time = time()
        res = func2wrap(*args)
        end_time = time()
        time_elapsed = end_time - start_time
        print("time elapsed: %s" % time_elapsed)
        return res
    return wrapped_func


# run a test on link related rest endpoints.
@timeit
def invoke_rest_service( rest_url ):
    sleep(2)
    sock = urllib.request.urlopen( rest_url )
    raw_data = sock.read().decode( "utf-8" )
    json_data = json.loads( raw_data )
    formatted_data = json.dumps( json_data, indent=4 )
    return formatted_data


# test against the comment api thing.
comment_url = "https://www.reddit.com/comments/6nw57.json"
res = invoke_rest_service( comment_url )
print(res)


# test a fullname id lookup.
by_id_url = "http://www.reddit.com/by_id/t3_qlqio.json"
res = invoke_rest_service( by_id_url )
print(res)

# test a profile lookup
profile_url = "http://www.reddit.com/user/pyglados/about.json"
res = invoke_rest_service( profile_url )
print( res )

# api info
api_info = "http://www.reddit.com/api/info.json"
res = invoke_rest_service( api_info )
print( res )

#test a subreddit lookup
subreddit_url = "http://www.reddit.com/r/mylittlepony/about.json"
res = invoke_rest_service( subreddit_url )
print( res )