import json
import logging
from functools import wraps
from time import sleep
from typing import Callable

import requests
from flask import current_app
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from jwt.algorithms import RSAAlgorithm

from weskit.login.oidcUser import User
from weskit.login.utils import onlineValidation
from weskit.login.loginConfigValidator import (
    isLoginEnabled,
    validate_setup_login_config,
    validate_received_config_or_stop
)
from weskit.classes.ErrorCodes import ErrorCodes

logger = logging.getLogger(__name__)


class oidcLogin:
    """
    This Class Initializes the OIDC Login and creates a flask_jwt_extended JWTManager. It allows a
    login with access token in the request header. It is not possible to directly login into the
     WESkit API. Use the WESkit Dashboard for a browsable login endpoint.
    """

    def __init__(self, app, config: dict):
        """

        app: Flask App object
        config: dictionary
        """

        app.OIDC_Login = self

        # Check if the Login System should be Initialized
        if isLoginEnabled(config):

            app.OIDC_Login = self
            validate_setup_login_config(app, self, config)

        else:

            return None

        # Request external configuration from Issuer URL
        config_url = "%s/.well-known/openid-configuration" % self.issuer_url

        for retry in range(4, -1, -1):
            try:
                self.oidc_config = requests.get(config_url).json()
                break

            except Exception as e:
                logger.info(
                    'Unable to load endpoint path from\n"%s"\n'
                    'Probably wrong url in config file or maybe json error will retry %d times' %
                    (config_url, retry)
                )

                if not retry:
                    logger.exception(
                        "Timeout! Could not receive configuration from the Identity Provider! "
                        "Stopping Server!")
                    logger.exception(e)
                    exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)
                sleep(20)

        # check existence of required information from Identity Provider or stop!
        validate_received_config_or_stop(self.oidc_config)

        logger.info("Loaded Issuer Config correctly!")

        # Use the obtained Issuer Config to obtain public key
        logger.info("Extracting Public Certificate from Issuer")

        try:
            self.oidc_jwks_uri_response = requests.get(self.oidc_config["jwks_uri"]).json()

        except Exception as e:
            logger.exception(
                "Could not connect to %s to receive the RSA public key!" %
                self.oidc_config["jwks_uri"])

            logger.exception(e)

            exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)

            # retrieve first jwk entry from jwks_uri endpoint and use it to
            # construct the RSA public key
        try:
            app.config["JWT_PUBLIC_KEY"] = RSAAlgorithm.from_jwk(
                json.dumps(self.oidc_jwks_uri_response["keys"][0]))

        except Exception as e:
            logger.exception(
                "An exception occurred during RSA key extraction from %s " %
                self.oidc_jwks_uri_response)

            logger.exception(e)
            logger.exception("The server will be stopped now!")

            exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)

        # Deactivate JWT CSRF since it is not working with external Identity Provider access tokens
        # It is reimplemented by this module
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False

        # Here here the flask_jwt_extended module will be initialized
        self.jwt = JWTManager(app)

        @self.jwt.user_loader_callback_loader
        def user_loader_callback(identity: str) -> User:
            """
            This function returns a User Object if the flask_jwt_extended current_user is called
            :param identity: unused, since data of access token will be used here but its required
            :return: User
            """

            return User()


def login_required(fn: Callable, validateOnline: bool = True) -> Callable:
    """
    This decorator checks if the login is initialized. If not all endpoints are exposed unprotected.
    Otherwise the decorator validates the access_token. If validateOnline==True the access_token
    will be validated by calling the identity provider. ValidateOnline==False will only check the
    certificate of the token offline. validateOnline should be true in high security cases that will
    cause changes in the backend. (cancelRun, submitRun)

    :param fn: render function
    :param validateOnline: bool should the identity provider asked for validity of the token?
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Don't use endpoint protection if LoginModule is not initialized
        if current_app.OIDC_Login is not None:

            # Check availability of access_token
            checkJWT = jwt_required(fn)(*args, **kwargs)

            if validateOnline:
                # make a request to oidc identity provider
                if onlineValidation():
                    return checkJWT
                else:
                    return {"msg": "Online Validation Failed, use new access_token"}, 401

            # in case of deactivated JWT ignore JWT validation
            return checkJWT

        return fn(*args, **kwargs)

    return wrapper
