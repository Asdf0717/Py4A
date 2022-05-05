from contextlib import contextmanager
 
from django.conf import settings
from django.db import connection
 
 
@contextmanager
def no_queries_allowed():
    """This is a helper method that makes it easier during development, by
    throwing an exception when any queries are made within its block.  Using
    an ORM, it's sometimes hard to discover what statements lead to implicit
    queries.  Wrapping this contextmanager around such blocks makes sure that
    this cannot happen.
 
    This is only works in debug mode, as in non-debug mode the
    connection.queries list isn't available for inspection.  In production,
    this is a no-op.
    """
    if settings.DEBUG:
        queries = connection.queries
        num_queries = len(queries)
    yield
    if settings.DEBUG:
        assert num_queries == len(queries), \
            "A query was made, but this was explicitly forbidden! " \
            "Queries were: {}".format(queries[num_queries:])
