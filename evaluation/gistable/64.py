#!/usr/bin/env python3

from functools import wraps
import json

# Pretend this was logging to disk
log = []

def mutator(fn):

    @wraps(fn)
    def logger(self, *args, **kwargs):
        self.log(fn.__name__, args, kwargs)

    logger.replay = lambda s, a, k: fn(s, *a, **k)

    return logger

class DB:

    def log(self, name, args, kwargs):
        entry = json.dumps({'name': name, 'args': args, 'kwargs': kwargs})
        log.append(entry)

    def replay(self, x):
        entry = json.loads(x)
        getattr(self.__class__, entry['name']).replay(self, entry['args'], entry['kwargs'])


class FooDB (DB):

    def __init__(self):
        self.state = dict()

    @mutator
    def blah(self, a, b):
        "Blah blah blah"
        self.state[a] = b

if __name__ == '__main__':

    f = FooDB()

    f.blah(10, 20);
    f.blah(30, 40)
    f.blah('abc', 'def')

    print('-- LOG --')
    for e in log: print(e)
    print('---------')

    for e in log: f.replay(e)

    print(f.state)
