from functools import wraps
from typing import Callable

from flask import current_app
from flask_jwt_extended import jwt_required

from weskit.oidc.utils import online_validation


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
