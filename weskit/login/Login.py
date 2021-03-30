import json
import logging

import requests
from time import sleep, time

from functools import wraps
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask import current_app, request

from jwt.algorithms import RSAAlgorithm

from weskit.login import oidcBlueprint as login_bp
from weskit.login.oidcUser import User
from weskit.login.utils import onlineValidation, check_csrf_token, getToken
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class oidcLogin:
    """
    This Class Initializes the OIDC Login and creates a JWTManager
    during initialisation multiple additional endpoints will be created
    for an manual login.
    """

    def __init__(self, app, config: dict, addLogin: bool = True):
        """

        :type addLogin: object
        app: Flask App object
        config: dictionary
        addLogin: enables login endpoints (bool)
        """

        app.OIDC_Login = self

        # Check if the Login System can be Initialized
        if (
            "login" in config and
            config['login'].get("enabled", False) and
            "jwt" in config['login'] and
            "oidc" in config['login']
        ):

            app.OIDC_Login = self

            # Flask_jwt_extended expect its configuration in the app.config object.
            # Therefore we copy the config to the app object.
            for key, element in config['login']['jwt'].items():
                app.config[key] = element

            self.issuer_url = config['login']['oidc']["OIDC_ISSUER_URL"]
            self.client_secret = config['login']['oidc']['OIDC_CLIENT_SECRET']
            self.hostname = config['login']['oidc']['OIDC_FLASKHOST']
            self.realm = config['login']['oidc']['OIDC_REALM']
            self.client_id = config['login']['oidc']['OIDC_CLIENTID']

        else:
            logger.warning("Login System Disabled")
            logger.warning(
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
        config_url = "%s/.well-known/openid-configuration" % self.issuer_url

        for retry in range(4, -1, -1):
            try:
                self.oidc_config = requests.get(config_url).json()
                break

            except Exception as e:
                logger.exception(
                    'Unable to load endpoint path from\n"%s"\n'
                    ' Probably wrong url in config file or maybe json error will retry %d times' % (config_url, retry)
                )
                logger.exception(e)

                if not retry:
                    logger.exception("Timeout! Could not receive config from the Identity Provider! Stopping Server!")
                    exit(42)
                sleep(20)

        # check existence of required information from Identity Provider or stop!
        validate_received_config_or_stop(self.oidc_config)

        logger.info("Loaded Issuer Config correctly!")

        # Use the obtained Issuer Config to obtain public key
        logger.info("Extracting public certificate from Issuer")

        try:
            self.oidc_jwks_uri_response = requests.get(self.oidc_config["jwks_uri"]).json()

        except Exception as e:
            logger.exception("Could not connect to %s to receive the RSA public key!" % self.oidc_config["jwks_uri"])
            logger.exception(e)
            exit(45)

            # retrieve first jwk entry from jwks_uri endpoint and use it to
            # construct the RSA public key
        try:
            app.config["JWT_PUBLIC_KEY"] = RSAAlgorithm.from_jwk(
                json.dumps(self.oidc_jwks_uri_response["keys"][0]))

        except Exception as e:
            logger.exception("An exception occurred during RSA key extraction from %s " % self.oidc_jwks_uri_response)
            logger.exception(e)
            logger.exception("The server will be stopped now!")
            exit(46)

        # Deactivate JWT CSRF since it is not working with external Identity Provider access tokens
        # It is reimplemented by this module
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False

        # Here here the flask_jwt_extended module will be initialized
        self.jwt = JWTManager(app)

        @self.jwt.user_loader_callback_loader
        def user_loader_callback(identity: str) -> User:
            """
            This function returns a User Object if the flask_jwt_extended current_user is called
            :param identity: unused, since data of access token will be used here
            :return: User
            """

            return User()

        if addLogin:
            """
            This code block is only used if the login endpoints should be accessible enabled on the server. The imports
            are only required for this specific scenario.
            """

            from flask_jwt_extended import get_raw_jwt

            logger.info("Creating Login Endpoints.")

            # Add Login Endpoints to the app the login endpoints are located at /login, login/logout, login/refresh
            app.register_blueprint(login_bp.login)

            if config.get("DEBUG", False):
                # In debug mode /login/test shows a demo of the current user object.
                from weskit.login import oidcDebugEndpoints as debugBP
                app.register_blueprint(debugBP.bp)

            @app.after_request
            def refresh_expiring_jwts(response: Callable) -> Callable:
                """
                This function checks if the access token cookie has exceeded the half of its expiration time. If the
                access token in a cookie is nearly gone the access token cookie will be refreshed as well as the refresh
                token and csrf token.

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
                        if time() > target_timestamp:
                            return login_bp.refresh_access_token(response_object=response)

                # Do nothing if no cookie is submitted or cookies are deleted
                return response
        else:
            logger.info("Will not Create Login Endpoint.")


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


def validate_received_config_or_stop(config: Any) -> Optional[dict]:
    """
    This function validates that the config received from the Identity Provider has the corect format and contains
    all required fields.
    :param config:
    :return:
    """

    if not isinstance(config, dict):
        logger.exception(
            "The configuration received from Identity Provider does not have the expected type dict!"
            "The type is %s. The server will be stopped now!" % str(type(config))
        )
        exit(43)

    required_values = [
            'authorization_endpoint',
            'token_endpoint',
            'jwks_uri'
    ]

    missing_values = [value for value in required_values if value not in config]
    if missing_values:
        logger.exception(
            "The config received from the Identity Provider does not contain the required"
            "information. The following keys are missing in the config [%s]\n"
            "The server will be stopped now!" % ', '.join(missing_values)
        )
        exit(44)

    return config
