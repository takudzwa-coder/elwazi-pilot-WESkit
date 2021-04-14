from flask import current_app, request, jsonify, make_response

from flask_jwt_extended.config import config
import requests
from flask_jwt_extended.utils import (
    decode_token,
    get_raw_jwt,
    set_access_cookies,
    set_refresh_cookies
)
from flask_jwt_extended.view_decorators import (
    _decode_jwt_from_cookies,
    _decode_jwt_from_headers)
from typing import Optional, Generic, List
import logging


def onlineValidation() -> bool:
    """
    checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    logger = logging.getLogger(__name__)
    app = current_app

    access_token = getToken()
    payload = {
        "client_id": app.OIDC_Login.client_id,
        "client_secret": app.OIDC_Login.client_secret,
        "token": access_token
    }
    try:
        # Make request
        j = requests.post(
            data=payload,
            url=app.OIDC_Login.oidc_config["introspection_endpoint"]
        ).json()

    except Exception as e:
        logger.exception(
            "Could not reach OIDC provider for online Validation"
        )
        logger.exception(e)

        return (False)

    return j.get('active', False)


def getToken(token_type: str = "access", locations: Optional[List[str]] = None) -> Optional[str]:
    """
    This function returns the encoded access_token from different sources.
    Its basically identical to a function from jwt_extended but has different
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
            return encoded_token
            break

        except Exception:
            # In case token not found for this method
            pass
    return None


def check_csrf_token() -> Optional[str]:
    """
    This function evaluates the csrf token.
    In case of success it returns None in error Cases it returns an
    string error message.
    If the cookie is submitted it will always be used as token
    choise. If only a header token is submitted this function will
    allways return None.
    """
    logger = logging.getLogger(__name__)

    cookieLoginbyCookie = (
            current_app.config["JWT_ACCESS_COOKIE_NAME"] in request.cookies
    )
    headerAuth = request.headers.get("Authorization", None)

    # Check token  is submitted by cookie:
    if cookieLoginbyCookie:
        jwt_cookie_sessionstate = get_raw_jwt().get("session_state", None)

        # Check session state in cookie
        if jwt_cookie_sessionstate is None:
            logger.warning(
                "access_token has not 'session_state' attribute"
            )
            return "Access Token does not have session_state"

        csfr_sessionstate = request.headers.get("X-CSRF-TOKEN", None)
        # Session token in Header is missing
        if csfr_sessionstate is None:
            logger.warning("Cookie login without csrf.")
            return (
                "Cookie Login detected: "
                "X-CSRF-TOKEN is not submitted via Header!"
            )

        # Session Token unequal
        if csfr_sessionstate != jwt_cookie_sessionstate:
            logger.info(
                "X-CSRF Token invalid"
            )
            return "X-CSRF-TOKEN is not matching the access Token"

        # Everything is OK
        return None

    # Header login is valid without csrf session token
    if headerAuth:
        return None

    # Unknown Error / Unsupported Method
    return "Unknown error"


def requester_and_cookieSetter(
        payload: str,
        setcookies: bool = True,
        response_object: Generic = None) -> Generic:

    # Make request
    try:
        j = requests.post(
            data=payload,
            url=current_app.OIDC_Login.oidc_config["token_endpoint"]
        ).json()

        # obtain access_token and refresh token from response
        at = j.get('access_token', None)
        rt = j.get('refresh_token', None)
        ate = j.get('expires_in', None)
        rte = j.get("refresh_expires_in", None)
        session_state = j.get("session_state", None)

        # In case of an invalid session or user logout return error
        if 'error' in j:
            if response_object:
                return response_object

            j['refresh'] = False

            return j, 401

        if not setcookies:

            if response_object:
                return response_object

            return j, 200

        if at and rt and session_state:
            # Set Cookie and Return
            if not response_object:
                response_object = make_response(({'login': True}, 200))

            set_access_cookies(response_object, at, ate)
            set_refresh_cookies(response_object, rt, rte)
            response_object.set_cookie("X-CSRF Token", session_state)

            return response_object

        else:
            if response_object:
                return response_object

            return {'login': False}, 401

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Login Process Failed")
        logger.exception(e)
        if response_object:
            return response_object
        return (jsonify(
            {'refresh': False, 'msg': 'Login Process Failed'}
        ), 401)
