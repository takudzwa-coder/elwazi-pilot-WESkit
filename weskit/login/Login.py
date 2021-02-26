import json
import logging
import requests

from functools import wraps
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, get_raw_jwt, verify_jwt_in_request
from flask import current_app

from jwt.algorithms import RSAAlgorithm

from login import oidcBlueprint as login_bp
from login.oidcUser import User
from login.utils import onlineValidation


class odicLogin:
    """ This Class Initializes the OIDC Login and creates a JWTManager
during initialisation multiple additional endpoints will be created
for an manual login
  """
    def __init__(self, app):
        app.OIDC_Login = self
        if not isinstance(app.logger, logging.Logger):
            self.logger = logging.getLogger("default")
        else:
            self.logger = app.logger

        # Check for ISSUER_URL in CONFIG
        if ("OIDC_ISSUER_URL" not in app.config):
            self.logger.error(
                'app.config["OIDC_ISSUER_URL"] is not set!'
            )
            exit(1)

        # Request URLS from ODIC Endpoint
        try:
            self.oidc_config = requests.get(
                app.config["OIDC_ISSUER_URL"] +
                "/.well-known/openid-configuration", verify=False
            ).json()

            # Check Existance of oidc config values
            self.oidc_config['authorization_endpoint']
            self.oidc_config["token_endpoint"]
            self.oidc_config["jwks_uri"]

        except KeyError as ke:
            self.logger.exception(
                (
                    'Unable to find required field in config!\nCheck'
                    '%s/.well-known/openid-configuration'
                ) % (app.config["OIDC_ISSUER_URL"])
            )
            self.logger.exception(ke)
            exit(1)

        except Exception as e:
            self.logger.exception(
                (
                    'Unable to load endpoint path from "%s'
                    '/.well-known/openid-configuration"\n Probably wrong '
                    'url in app.config["OIDC_ISSUER_URL"] or json error'
                ) % (app.config["OIDC_ISSUER_URL"])
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

        # Add Login blueprint and Setup JWTManager
        app.register_blueprint(login_bp.login)
        self.jwt = JWTManager(app)

        # Define Custom jwt callback functions
        @self.jwt.user_loader_callback_loader
        def user_loader_callback(identity):
            u = User()
            return(u)


def login_required(fn, validateOnline=True):
    """
    this function checks if the login is initialized. If not all endpoints
    were not protected.
    Otherwise the function checks if an access_token is available
    validateOnline should be true in high security cases (as workflow
    submittions) validateOnline can be false for status requests.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Don't use endpoint protection if Loginin is not initialized
        if current_app.OIDC_Login is not None:
            #
            if validateOnline:
                # Check availablility of access_token
                checkJWT = jwt_required(fn)(*args, **kwargs)
                if onlineValidation():
                    return checkJWT
                else:
                    return(
                        json.dumps(
                            {"msg":"Online Validation Failed, use new access_token"}  # noqa E501
                        ), 401
                    )
            # in case of deactivated JWT ignore JWT validation
            return checkJWT

        return fn(*args, **kwargs)

    return wrapper


def group_required(group=""):
    """
    This function checks the Client specific Role for a specified group
    If group was FOUND the Endpoind will be returned
    If group MISSING a 403 error will be returned
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # standard flask_jwt_extended token verifications
            verify_jwt_in_request()

            # custom group membership verification
            # Probably, needs to be changed in LDAP context!
            # print(get_raw_jwt())
            groups = get_raw_jwt().get(
                'resource_access',
                dict()
            ).get(
                current_app.config["OIDC_CLIENTID"],
                dict()
            ).get('roles', dict())
            # print (groups)
            if group not in groups:
                return (
                    json.dumps(
                        {
                            "result": "user not in group'%s' required "
                            "to access this endpoint" % group
                        }
                    ),
                    403,
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
