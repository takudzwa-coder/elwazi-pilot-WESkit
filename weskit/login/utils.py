from flask import current_app

from flask_jwt_extended.config import config
import requests
from flask_jwt_extended.utils import decode_token
from flask_jwt_extended.view_decorators import (
    _decode_jwt_from_cookies,
    _decode_jwt_from_query_string,
    _decode_jwt_from_headers,
    _decode_jwt_from_json)


def onlineValidation():
    """
    checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    app = current_app

    access_token = getToken()
    header = {"Content-Type:" "application/x-www-form-urlencoded"}
    payload = {
            "client_id": app.config["OIDC_CLIENTID"],
            "client_secret": app.config['JWT_SECRET_KEY'],
            "token": access_token
    }
    try:
        # Make request
        j = requests.post(
            data=payload,
            header=header,
            url=app.OIDC_Login.oidc_config["introspection_endpoint"]
            ).json()
        print(j)
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
        if location == "query_string":
            get_encoded_token_functions.append(_decode_jwt_from_query_string)
        if location == "headers":
            get_encoded_token_functions.append(_decode_jwt_from_headers)
        if location == "json":
            get_encoded_token_functions.append(
                lambda: _decode_jwt_from_json(token_type)
            )

    for get_encoded_token_function in get_encoded_token_functions:
        try:
            encoded_token, csrf_token = get_encoded_token_function()
            decode_token(encoded_token, csrf_token)
            return(encoded_token)
            break
        except Exception as e:
            current_app.OIDC_Login.logger.exception(e)
    return(None)
