"""Flask extension utility."""

from flask.sessions import SessionInterface, SessionMixin
from werkzeug.contrib.cache import MemcachedCache

import memcache  # Use https://code.launchpad.net/~songofacandy/python-memcached/mixin-threading

def setup_cache(app):
    """
    Setup ``app.cache``.
    """
    # TODO: Support other cache type.
    servers = app.config.get('MEMCACHED_SERVERS', '').split()
    if not servers:
        servers = ['localhost:11211']
    servers = memcache.LockingClient(servers)

    prefix = app.config.get('MEMCACHED_PREFIX', '')
    app.cache = MemcachedCache(servers=servers, key_prefix=prefix)


class CacheSession(dict, SessionMixin):
    def __init__(self, session_key):
        self._session_key = session_key

class CacheSessionInterface(SessionInterface):
    """
    Store session in ``app.cache``
    """
    def __init__(self, key, prefix='session-'):
        SessionInterface.__init__(self)
        self._key_func = key
        self._prefix = prefix

    def open_session(self, app, request):
        cache = app.cache
        try:
            _key = self._prefix + self._key_func(request)
        except Exception:
            return None
        obj = cache.get(_key)
        if obj is None:
            obj = CacheSession(_key)
        return obj

    def save_session(self, app, session, response):
        cache = app.cache
        _key = session._session_key
        cache.set(_key, session, timeout=0)


# Example:
# app.config.update(MEMCACHED_SERVERS='localhost:11211 localhost:11212',
#                   MEMCACHED_PREFIX ='app32-',
#                   )
# setup_cache(app)
# app.session_interface = CacheSessionInterface(
#         key=lambda req: req.args.get('opensocial_viewer_id'),
#         )
# # Use cache.
# app.cache.set('foo', 'bar')
# # Use session
# flask.session.set('foo', 'bar')