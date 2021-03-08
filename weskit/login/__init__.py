from flask import (
    jsonify, redirect, render_template, current_app, request
)
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies, current_user
)
from typing import Union, Any, Callable
from functools import wraps


# In case of a successful login this function sets the login cookies.
# It redirects the user to a start page for a given redictURL or,
# it returns 200 {'login':true}

def setCookies(user: str, redictURL: Union[str, None] = None) -> tuple:
    # Create the tokens we will be sending back to the user
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    # Set the JWTs and the CSRF double submit protection cookies
    # in this response

    resp = jsonify({'login': True})
    if redictURL:
        resp = redirect(redictURL, code=302)
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    if redictURL:
        return resp
    return resp, 200


# By default, the CRSF cookies will be called csrf_access_token and
# csrf_refresh_token, and in protected endpoints we will look for the
# CSRF token in the 'X-CSRF-TOKEN' header. You can modify all of these
# with various app.config options. Check the options page for details.


# With JWT_COOKIE_CSRF_PROTECT set to True, set_access_cookies() and
# set_refresh_cookies() will now also set the non-httponly CSRF cookies
# as well

def login(request: request) -> tuple:
    # Auth via Script
    # returns 401 and {login:false}
    # or 200 and {login:true}
    if request.is_json:
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        authres = current_app.authObject.authenticate(username, password)
        if not authres:
            return jsonify({'login': False}), 403
        return(setCookies(authres))

    # Manual Auth via HTML forms
    # returns 401 and the login page again
    # or 302 and a welcome page in case of success
    elif len(request.form):
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        authres = current_app.authObject.authenticate(username, password)
        if not authres:
            return render_template('loginForm.html', hideHint="wrongHint"), 403
        return(setCookies(authres, "/ga4gh/wes/user_status"))
    # Fallback
    return jsonify({'login': False}), 403


# Because the JWTs are stored in an httponly cookie now, we cannot
# log the user out by simply deleting the cookie in the frontend.
# We need the backend to send us a response to delete the cookies
# in order to logout. unset_jwt_cookies is a helper function to
# do just that.
def logout() -> tuple:
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200


def refresh() -> tuple:
    # Create the new access token
    current_user2 = current_user
    access_token = create_access_token(identity=current_user2)

    # Set the access JWT and CSRF double submit protection cookies
    # in this response
    resp = jsonify({'refresh': True})
    set_access_cookies(resp, access_token)
    return resp, 200


# Switch for activating/deactivating Login
# Here is a custom decorator that verifies the JWT is present in
# the request, if 'JWT_SECRET_KEY' is specified
def login_required(
        fn: Callable[..., Any]
) -> Union[Callable[..., Any], tuple]:

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_app.config.get("JWT_ENABLED", True):
            checkJWT = jwt_required(fn)
            return checkJWT(*args, **kwargs)
        # in case of deactivated JWT ignore JWT validation
        return fn(*args, **kwargs)

    return wrapper
