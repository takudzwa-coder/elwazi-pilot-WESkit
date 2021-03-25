import json
import logging

import requests
import os

from functools import wraps
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask import current_app, request

from jwt.algorithms import RSAAlgorithm

from weskit.login import oidcBlueprint as login_bp
from weskit.login.oidcUser import User
from weskit.login.utils import onlineValidation, check_csrf_token, getToken
from typing import Callable


class oidcLogin:
    """
    This Class Initializes the OIDC Login and creates a JWTManager
    during initialisation multiple additional endpoints will be created
    for an manual login.
    """

    def __init__(self, app, config: dict, addLogin: bool = True):
        app.OIDC_Login = self
        self.logger = logging.getLogger(__name__)

        ##############################################
        # Configure Login
        ##############################################
        if (
            "login" in config and
            config['login'].get("enabled", False) and
            "jwt" in config['login'] and
            "oidc" in config['login']
        ):

            app.OIDC_Login = self

            # the JWT config is expected to be in the app config
            for key, element in config['login']['jwt'].items():
                app.config[key] = element

            # for key, element in config['login']['oidc'].items():
            #    app.config[key] = element

            self.issuer_url = config['login']['oidc']["OIDC_ISSUER_URL"]
            self.client_secret = config['login']['oidc']['OIDC_CLIENT_SECRET']
            self.hostname = config['login']['oidc']['OIDC_FLASKHOST']
            self.realm = config['login']['oidc']['OIDC_REALM']
            self.client_id = config['login']['oidc']['OIDC_CLIENTID']

            # Check if we are in test case
            if os.environ.get("kc_backend", False):
                self.issuer_url = os.environ["kc_backend"]

        else:
            self.logger.warning("Login System Disabled")
            self.logger.warning(
                    """login:{}
                    enabled:{}
                    jwt:{}
                    oidc:{}""".format(
                        "login" in config,
                        config['login'].get("enabled", False),
                        "jwt" in config['login'],
                        "oidc" in config['login'])
            )
            return None

        # Request external configuration from Issuer URL
        try:
            self.oidc_config = requests.get(
                self.issuer_url + "/.well-known/openid-configuration"
            ).json()

            # Check Existence of oidc config values
            self.oidc_config['authorization_endpoint']
            self.oidc_config["token_endpoint"]
            self.oidc_config["jwks_uri"]

        except Exception as e:
            self.logger.exception(
                (
                    'Unable to load endpoint path from "%s'
                    '/.well-known/openid-configuration"\n Probably wrong '
                    'url in config file or json error'
                ) % (self.issuer_url)
            )
            self.logger.exception(e)
            exit(1)

        self.logger.info("Loaded Issuer Config correctly!")

        # Use the obtained Issuer Config to obtain public key
        self.logger.info("Extracting public certificate from Issuer")

        try:
            self.oidc_jwks_uri = requests.get(self.oidc_config["jwks_uri"]).json()

            # retrieve first jwk entry from jwks_uri endpoint and use it to
            # construct the RSA public key
            app.config["JWT_PUBLIC_KEY"] = RSAAlgorithm.from_jwk(
                json.dumps(self.oidc_jwks_uri["keys"][0])
            )

        except Exception as e:
            self.logger.exception("Could not extract RSA public key!")
            self.logger.exception(e)
            exit(1)

        if addLogin:
            self.logger.info("Creating Login Endpoints.")

            # Add Login Endpoints to the app
            app.register_blueprint(login_bp.login)

            if config.get("DEBUG", False):
                from weskit.login import oidcDebugEndpoints as debugBP
                app.register_blueprint(debugBP.bp)

        else:
            self.logger.info("Will not Create Login Endpoint.")

        # Deactivate  JWT CSRF since it is not working with external oidc
        # access tokens
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        self.jwt = JWTManager(app)

        @self.jwt.user_loader_callback_loader
        def user_loader_callback(identity: str) -> User:
            """
            This function returns a User Object if the flask_jwt_extended current_user is called
            :param identity: unused, since data of access token will be used here
            :return: User
            """

            u = User()
            return (u)

        if addLogin:
            """
            This code block is only used if the login endpoints should be accessible enabled on the server. The imports
            are only required for this specific scenario.
            """

            from flask_jwt_extended import get_raw_jwt
            import time

            @app.after_request
            def refresh_expiring_jwts(response: Callable) -> Callable:
                """
                This function checks if the access token cookie has exceeded the half of its expiration time. If it's
                yes the access token in the cookie as well as the refresh token and csrf token will be replaced.

                :param response: render function
                :return: same as input potentially added new cookies.
                """
                # Do only something if JWT is transmitted via access_token cookie
                if current_app.config["JWT_ACCESS_COOKIE_NAME"] in request.cookies:

                    # Get the generation time and expiration time of the token
                    jwt_expiration_time = get_raw_jwt().get("exp", None)
                    jwt_last_refresh = get_raw_jwt().get("iat", None)

                    # Test for existence of both values critical at logout
                    if jwt_expiration_time and jwt_last_refresh:

                        # Refresh cookies if it reaches half of lifetime
                        target_timestamp = (jwt_expiration_time + jwt_last_refresh) / 2
                        if time.time() > target_timestamp:
                            return login_bp.refresh_access_token(response_object=response)

                # Do nothing if no cookie is submitted or cookies are deleted
                return response


def login_required(fn: Callable, validateOnline: bool = True, validate_csrf: bool = True) -> Callable:
    """
    This decorator checks if the login is initialized. If not all endpoints are exposed unprotected.
    Otherwise the decorator validates the access_token. If validateOnline==True the access_token will be validated by
    calling the identity provider. ValidateOnline==False will only check the certificate of the token offline.
    validateOnline should be true in high security cases that will cause changes in the backend. (cancelRun, submitRun)
    Also validate_csrf must be true high security cases. In this cases the client must write the "X-CSRF-TOKEN" to the
    request header!

    :param fn: render function
    :param validateOnline: bool should the identity provider asked for validity of the token?
    :param validate_csrf: bool should be the CSRF token be checked? (Imported at non only viewing calls)
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Don't use endpoint protection if LoginModule is not initialized
        if current_app.OIDC_Login is not None:

            # Check availability of access_token
            checkJWT = jwt_required(fn)(*args, **kwargs)
            csrf_state = check_csrf_token()

            # Check if csrf must be checked
            if validate_csrf:
                csrf_state = check_csrf_token()
                if csrf_state:
                    return {"msg": csrf_state}, 401

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


def AutoLoginUser(fn: Callable, validateOnline: bool = True) -> Callable:
    """
    This decorator redirects the user to the login form of the oidc identity provider and back to the requested page.
    The client receives an access_token cookie, refresh_token cookie and CSRF token cookie.
    In the case that the client has already an access_token this function is checks the validity of the token but not
    of the CSRF token. Otherwise you would have to submit the CSRF token in header at every request!
    :param fn: render function
    :return: render function
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # If there is no loadable token
        if current_app.OIDC_Login is None:
            raise Exception('OIDC_Login must be initialized before using the "AutoLoginUser" decorator')

        if not getToken():

            # use the function of the login endpoint and provide a redirect url
            return login_bp.loginFct(requestedURL=request.full_path)
        else:
            return login_required(fn, validateOnline=validateOnline, validate_csrf=False)(*args, **kwargs)

    return wrapper
