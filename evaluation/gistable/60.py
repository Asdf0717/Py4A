from django.conf import settings
from django.utils.importlib import import_module
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY

def request_factory_login(factory, user, backend='django.contrib.backends.ModelBackend'):
    engine = import_module(settings.SESSION_ENGINE)
    factory.session = engine.SessionStore()
    request.session[SESSION_KEY] = user.id
    request.session[BACKEND_SESSION_KEY] = backend
    factory.session.save()
    session_cookie = settings.SESSION_COOKIE_NAME
    factory.cookies[session_cookie] = request.session.session_key
    