# This experiment demonstrates the penalty of incorrect invocation of logger.
# You *CAN* kill your production instance with log.debug('some string %s' % (arg))
# even if str(arg) is cheap and loglevel is set to something higher than DEBUG.

# SEE ALSO: https://docs.python.org/3/howto/logging.html#optimization

import functools
import logging
import timeit

def correct_logging(obj):
    logging.debug('A simple log %s', obj)

def incorrect_logging(obj):
    logging.debug('A simple log %s' % (obj,))

def newstyle_incorrect_logging(obj):
    logging.debug('A simple log {}'.format(obj,))

class Message(object):
    def __str__(self):
        return "message"

for obj in "message", Message():
    print("#%r" % obj)
    for f in (correct_logging, incorrect_logging, newstyle_incorrect_logging):
        farg = functools.partial(f, obj)
        print("%30s: %.2fms" % (f.__name__, 1000*min(timeit.repeat(farg))))