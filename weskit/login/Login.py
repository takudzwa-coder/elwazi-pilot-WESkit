import json
import logging
import requests
import os

from functools import wraps
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, get_raw_jwt, verify_jwt_in_request
from flask import current_app, request

from jwt.algorithms import RSAAlgorithm

from weskit.login import oidcBlueprint as login_bp
from weskit.login.oidcUser import User
from weskit.login.utils import onlineValidation, check_csrf_token, getToken


class oidcLogin:
    """ This Class Initializes the OIDC Login and creates a JWTManager
during initialisation multiple additional endpoints will be created
for an manual login
  """

    def __init__(self, app, config, addLogin=True):
        app.OIDC_Login = self
        if not isinstance(app.logger, logging.Logger):
            self.logger = logging.getLogger("default")
        else:
            self.logger = app.logger

        ##############################################
        # Configure Login
        ##############################################
        if (
            "login" in config and
            config['login'].get("enabled", False) and
            "jwt" in config['login'] and
            "oidc" in config['login']
        ):

            # the JWT config is expected to be in the app config
            for key, element in config['login']['jwt'].items():
                app.config[key] = element

            # for key, element in config['login']['oidc'].items():
            #    app.config[key] = element

            self.issuer_url = config['login']['oidc']["OIDC_ISSUER_URL"]
            self.client_secret = config['login']['oidc']['OIDC_CIENT_SECRET']
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
                        "oidc" in config['login']))
                return None

        # Request URLS from ODIC Endpoint
        try:
            self.oidc_config = requests.get(
                self.issuer_url + "/.well-known/openid-configuration",
                verify=False
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
            self.oidc_jwks_uri = requests.get(
                self.oidc_config["jwks_uri"],
                verify=False
            ).json()

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
            # Add Login blueprint and Setup JWTManager
            app.register_blueprint(login_bp.login)
        else:
            self.logger.info("Will not Create Login Endpoint.")

        # Deactivate  JWT CSRF since it is not working with external oidc
        # access tokens
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        self.jwt = JWTManager(app)

        # Define Custom jwt callback functions
        @self.jwt.user_loader_callback_loader
        def user_loader_callback(identity):
            u = User()
            return (u)

        if addLogin:
            """
            This code block is only used if the login endpoints are enabled on the server. The imports are only required
            for this specific scenario.
            """
            from flask_jwt_extended import get_raw_jwt
            import time

            @app.after_request
            def refresh_expiring_jwts(response):
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


def login_required(fn, validateOnline=True, validate_csrf=True):
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

            # Check if csrf musst be checked
            if validate_csrf and csrf_state:
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


def group_required(group=""):
    """
    This function checks the Client specific Role for a specified group
    If group was FOUND the Endpoint will be returned
    If group MISSING a 403 error will be returned
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # standard flask_jwt_extended token verifications
            verify_jwt_in_request()

            # custom group membership verification
            # Probably, needs to be changed in LDAP context!
            groups = get_raw_jwt().get(
                'resource_access',
                dict()
            ).get(
                current_app.config["OIDC_CLIENTID"],
                dict()
            ).get('roles', dict())
            # print (groups)
            if group not in groups:
                return {"result": "user not in group'%s' required to access this endpoint" % group}, 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def AutoLoginUser(fn, validateOnline=True):
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
        if not getToken():

            # use the function of the login endpoint and provide a redirect url
            return login_bp.loginFct(requestedURL=request.full_path)
        else:
            return login_required(fn, validateOnline=validateOnline, validate_csrf=False)(*args, **kwargs)

    return wrapper
