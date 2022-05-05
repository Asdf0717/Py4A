import time
import datetime

def datetime_to_timestamp(datetime_ob):
    return time.mktime(datetime_ob.timetuple())

def datetime_from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)