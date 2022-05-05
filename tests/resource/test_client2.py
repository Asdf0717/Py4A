"""Test more corner cases in client API usage extraction."""

import a
import b
import c1.c2 as c1, c1.c3 as c2
from d1.d2 import d1 as d3, d2 as d4


def foo():
    a = c1()
    b = c2()
    a(), b()


def bar():
    d3(a.foo(), b.bar(0))
    a = d4
    x = dict()
    a(*x, **x)
