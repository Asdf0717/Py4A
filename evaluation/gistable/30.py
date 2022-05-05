import random
from flask import request, session, abort, Markup

@app.template_global('csrf_token')
def csrf_token():
    """
    Return the CSRF token for the current session

    If not already generated, session["_csrf_token"] is set to a random
    string. The token is used for the whole life of the session.
    """

    if "_csrf_token" not in session:
        session["_csrf_token"] = hex(random.getrandbits(64))
    return session["_csrf_token"]

@app.template_global('csrf_token_input')
def csrf_token_input():
    """Returns a hidden input element with the CSRF token"""
    return Markup('<input type="hidden" name="_csrf_token" value="{0}">') \
            .format(csrf_token())

def check_csrf_token():
    """Checks that request.form["_csrf_token"] is correct, aborting if not"""
    if "_csrf_token" not in request.form:
        logger.warning("Expected CSRF Token: not present")
        abort(400)
    if request.form["_csrf_token"] != csrf_token():
        logger.warning("CSRF Token incorrect")
        abort(400)

@app.before_request
def auto_check_csrf():
    if request.method == "POST" or request.form:
        check_csrf_token()
