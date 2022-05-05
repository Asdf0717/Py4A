import webapp2

from webapp2_extras import local

_local = local.Local()

# The deferred handler instantiates webapp2.WSGIApplication in the module
# globals, so when it is imported it ends resetting app globals.
# To avoid this we duplicate the globals part of the WSGIApplication here,
# knowing that only we will instantiate it.

class WSGIApplication(webapp2.WSGIApplication):
    def set_globals(self, app=None, request=None):
        _local.app = app
        _local.request = request

    def clear_globals(self):
        _local.__release_local__()

def get_app():
    return _local.app

def get_request():
    return _local.request