#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
from functools import wraps
from typing import Callable, Optional

import requests
from flask import current_app
from flask_jwt_extended.view_decorators import _decode_jwt_from_headers, verify_jwt_in_request

logger = logging.getLogger(__name__)


def login_required(validate_online: bool = True):
    """
    This decorator checks if the login is initialized. If not all endpoints are exposed
    unprotected. Otherwise, the decorator validates the access_token. If validateOnline==True
    the access_token will be validated by calling the identity provider. ValidateOnline==False
    will only check the certificate of the token offline. validateOnline should be true in
    high security cases that will cause changes in the backend. (cancelRun, submitRun)

    Compare: https://flask-jwt-extended.readthedocs.io/en/stable/custom_decorators/

    :param validate_online: bool should the identity provider asked for validity of the token?
    """

    def wrapper(fn: Callable):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_app.oidc_login is None:
                # Don't use endpoint protection!
                verify_jwt_in_request(optional=True)
            else:
                verify_jwt_in_request()
                if validate_online:
                    if not validate(current_app):
                        return {"msg": "Online validation failed"}, 401
            return fn(*args, **kwargs)

        return decorator

    return wrapper


def validate(app) -> bool:
    """
    Checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    access_token = get_token()
    payload = {
        "client_id": app.oidc_login.client_id,
        "client_secret": app.oidc_login.client_secret,
        "token": access_token
    }
    try:
        j = requests.post(
            data=payload,
            url=app.oidc_login.introspection_endpoint
        ).json()

    except Exception as e:
        logger.error("Could not reach OIDC provider for online validation", exc_info=e)
        return False

    if j.get('active', False):
        return True
    else:
        logger.warning("Online validation failed: id='{}', secret='{}', token='{}'".
                       format(current_app.oidc_login.client_id,
                              current_app.oidc_login.client_secret,
                              get_token()))
        return False


def get_token(token_type: str = "access") -> Optional[str]:   # nosec B107, token_type no problem
    """
    This function returns the encoded access_token from different sources.
    It is basically identical to a function from jwt_extended but has different
    return
    """

    try:
        encoded_token, csrf_token = _decode_jwt_from_headers()
        # Maybe _decode_jwt_from_request(token_type)?
    except Exception:  # TODO Check: Can this be InvalidHeaderError?
        # If Token is not in header
        encoded_token = None
    return encoded_token
