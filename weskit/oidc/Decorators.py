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
import json
from flask import current_app
from flask_jwt_extended import jwt_required
from flask_jwt_extended.view_decorators import _decode_jwt_from_headers

logger = logging.getLogger(__name__)


def login_required(fn: Callable,
                   validate_online: bool = True)\
        -> Callable:
    """
    This decorator checks if the login is initialized. If not all endpoints are exposed unprotected.
    Otherwise the decorator validates the access_token. If validateOnline==True the access_token
    will be validated by calling the identity provider. ValidateOnline==False will only check the
    certificate of the token offline. validateOnline should be true in high security cases that will
    cause changes in the backend. (cancelRun, submitRun)

    :param fn: render function
    :param validate_online: bool should the identity provider asked for validity of the token?
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Don't use endpoint protection if LoginModule is not initialized
        if current_app.oidc_login is not None:

            # Check availability of access_token
            checkJWT = jwt_required(fn)(*args, **kwargs)

            if validate_online:
                # make a request to oidc identity provider
                if online_validation(current_app):
                    return checkJWT
                else:
                    return {"msg": "Online validation failed. Use new access_token"}, 401

            # in case of deactivated JWT ignore JWT validation
            return checkJWT

        return fn(*args, **kwargs)

    return wrapper


def online_validation(app) -> bool:
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
        logger.exception("Could not reach OIDC provider for online validation")
        logger.exception(e)
        return False
    if j.get('active', False):
        return True
    else:
        logger.info("User validation at {} failed.".format(app.oidc_login.introspection_endpoint))
        logger.info(json.dumps(j))
        return False




def get_token(token_type: str = "access") -> Optional[str]:   # nosec B107, token_type no problem
    """
    This function returns the encoded access_token from different sources.
    Its basically identical to a function from jwt_extended but has different
    return
    """

    try:
        encoded_token, csrf_token = _decode_jwt_from_headers()
        # Maybe _decode_jwt_from_request(token_type)?
    except Exception:  # TODO Check: Can this be InvalidHeaderError?
        # If Token is not in header
        encoded_token = None
    return encoded_token
