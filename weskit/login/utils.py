from flask import current_app, request

from flask_jwt_extended.config import config
import requests
from flask_jwt_extended.utils import decode_token, get_raw_jwt
from flask_jwt_extended.view_decorators import (
    _decode_jwt_from_cookies,
    _decode_jwt_from_headers)


def onlineValidation():
    """
    checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    app = current_app

    access_token = getToken()
    payload = {
            "client_id": app.config["OIDC_CLIENTID"],
            "client_secret": app.config["OIDC_CIENT_SECRET"],
            "token": access_token
    }
    try:
        # Make request
        j = requests.post(
            data=payload,
            url=app.OIDC_Login.oidc_config["introspection_endpoint"]
            ).json()

    except Exception as e:
        app.OIDC_Login.logger.exception(
            "Could not reach OIDC provider for online Validation"
        )
        app.OIDC_Login.logger.exception(e)
        return(False)

    return j.get('active', False)


def getToken(token_type="access", locations=None):
    """
    This function returns the encoded access_token from different sources.
    Its basicaly identical to a function from jwt_extended but has diffrent
    return
    """
    # All the places we can get a JWT from in this request
    get_encoded_token_functions = []

    # Get locations in the order specified by the decorator or
    # JWT_TOKEN_LOCATION
    # configuration.
    if not locations:
        locations = config.token_location

    # Add the functions in the order specified by locations.
    for location in locations:
        if location == "cookies":
            get_encoded_token_functions.append(
                lambda: _decode_jwt_from_cookies(token_type)
            )
        if location == "headers":
            get_encoded_token_functions.append(_decode_jwt_from_headers)


    for get_encoded_token_function in get_encoded_token_functions:
        try:
            encoded_token, csrf_token = get_encoded_token_function()
            decode_token(encoded_token, csrf_token)
            return(encoded_token)
            break
        except Exception as e:
            # In case token not found for this method
            pass
    return(None)


def check_csrf_token():
    """
    This function evaluates the csrf token.
    In case of success it returns None in error Cases it returns an
    string error message.
    If the cookie is submitted it will allways be used as token
    choise. If only a header token is submitted this function will
    allways return None. 
    """

    cookieLoginbyCookie = current_app.config["JWT_ACCESS_COOKIE_NAME"] in request.cookies
    headerAuth = request.headers.get("Authorization",None)

    # Check token  is submitted by cookie:
    if cookieLoginbyCookie:
        jwt_cookie_sessionstate = get_raw_jwt().get("session_state",None)
        # Check session state in cookie
        if jwt_cookie_sessionstate is None:
            current_app.OIDC_Login.logger.warning(
                "access_token has not 'session_state' attribute"
            )
            return ("Access Token does not have session_state")

        csfr_sessionstate = request.headers.get("X-CSRF-TOKEN",None)
        # Session token in Header is missing
        if (csfr_sessionstate is None):
            current_app.OIDC_Login.logger.warning("Cookie login without csrf.")
            return ("Cookie Login detected: X-CSRF-TOKEN is not submitted via Header!")

        # Session Token unequal
        if csfr_sessionstate !=jwt_cookie_sessionstate:
            current_app.OIDC_Login.logger.info(
            "X-CSRF Token invalid"
            )
            return("X-CSRF-TOKEN is not matching the access Token")
        # Everything is OK
        return(None)

    # Header login is valid without csrf session token
    if headerAuth:
        return(None)
    # Unknown Error / Unsupported Method
    return ("Unknown error")

def requester_and_cookieSetter(payload,setcookies=True):
    # Make request
    try:
        j = requests.post(
            data=payload,
            url=app.OIDC_Login.oidc_config["token_endpoint"]
        ).json()
        print(app.OIDC_Login.oidc_config["token_endpoint"])
        print(j)
        # obtain access_token and refresh token from response
        at = j.get('access_token', None)
        rt = j.get('refresh_token', None)
        ate = j.get('expires_in', None)
        rte = j.get("refresh_expires_in", None)
        session_state = j.get("session_state", None)
            # In case of an invalid session or user logout return error
        if 'error' in j:
            j['refresh'] = False
            return(jsonify(j), 401)
            
        if not setcookies:
            return(jsonify(j),200)
        
        if at and rt and session_state:
            # Set Cookie and Return
            resp = jsonify({'login': True})
            set_access_cookies(resp, at, ate)
            set_refresh_cookies(resp, rt, rte)
            resp.set_cookie("X-CSRF Token",session_state)
            return(resp, 200)
        
        else:
            resp = jsonify({'login': False})
            return(resp, 401)
    except Exception as e:
        app.OIDC_Login.logger.exception("Login Process Failed")
        app.OIDC_Login.logger.exception(e)
        return(jsonify(
            {'refresh': False, 'msg': 'Login Process Failed'}
        ), 401)

