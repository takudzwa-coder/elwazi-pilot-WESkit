# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import logging
from functools import wraps
from typing import Callable, Optional

import requests
from flask import current_app as flask_current_app
from flask_jwt_extended.view_decorators import _decode_jwt_from_headers, verify_jwt_in_request

from weskit.utils import mop
from weskit.classes.WESApp import WESApp

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
            current_app = WESApp.from_current_app(flask_current_app)
            if current_app.oidc_login is None:
                # Don't use endpoint protection by OIDC.
                verify_jwt_in_request(optional=True)
            else:
                # An OIDC login is configured.
                verify_jwt_in_request()
                if validate_online:
                    if not validate(current_app):
                        return {"msg": "Online validation failed"}, 401
                    if not validate_userinfo(current_app):
                        return {"msg": "Userinfo validation failed"}, 401
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
            url=app.oidc_login.introspection_endpoint,
            timeout=60
        ).json()

    except Exception as e:
        logger.error("Could not reach OIDC provider for online validation", exc_info=e)
        return False

    if j.get('active', False):
        return True
    else:
        current_app = WESApp.from_current_app(flask_current_app)
        logger.warning("Online validation failed: id='{}', secret='{}', token='{}'".
                       format(mop(current_app.oidc_login, lambda login: login.client_id),
                              mop(current_app.oidc_login, lambda login: login.client_secret),
                              get_token()))
        return False


def validate_userinfo(app) -> bool:

    if (app.config["userinfo_validation_claim"] is None and
            app.config["userinfo_validation_value"] is None):
        return True

    access_token = get_token()
    header = {"Authorization": "Bearer " + str(access_token)}

    try:
        claim_response = requests.get(
            url=app.oidc_login.userinfo_endpoint,
            headers=header,
            timeout=60
        ).json()
    except Exception as e:
        logger.error("Could not reach OIDC provider for userinfo validation", exc_info=e)
        return False

    test_claim = claim_response[app.config["userinfo_validation_claim"]]

    if app.config["userinfo_validation_value"] in test_claim:
        return True
    else:
        current_app = WESApp.from_current_app(flask_current_app)
        logger.warning("Userinfo validation failed: id='{}', secret='{}', token='{}'".
                       format(mop(current_app.oidc_login, lambda login: login.client_id),
                              mop(current_app.oidc_login, lambda login: login.client_secret),
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
