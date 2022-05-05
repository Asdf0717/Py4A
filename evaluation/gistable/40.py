#-*- coding:utf-8 -*-
from functools import wraps
import inspect


def auto_attr_init(f):
    @wraps(f)
    def _auto_attr_init(*args, **kwargs):
        arg_values = args[1:] + inspect.getargspec(f).defaults
        for pair in zip(f.__code__.co_varnames[1:], arg_values):
            setattr(args[0], pair[0], pair[1])
    return _auto_attr_init


class Point(object):
    @auto_attr_init
    def __init__(self, x, y=10): pass


if __name__ == '__main__':
    p = Point(2, 4)
    assert p.x == 2
    assert p.y == 4
    p = Point(2)
    assert p.y == 10