import json
import logging
import os
from time import sleep

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from flask import Flask
from flask_jwt_extended import JWTManager
from jwt.algorithms import RSAAlgorithm

from weskit import Login
from weskit.oidc.User import User

logger = logging.getLogger(__name__)


def is_login_enabled(config: dict) -> bool:
    """
    This function checks if all required configurations are set end enabled in the config file
    It returns true if the Login is correctly set up end enabled, otherwise false

    :param config: configuration dict
    :return:
    """
    # Check whether the Login System can be initialized
    if ("login" in config and
            config['login'].get("enabled", False) and
            "jwt" in config['login']):
        return True

    else:
        logger.warning("Login System Disabled")
        logger.warning(
            """login:{}
            enabled:{}
            jwt:{}""".format(
                "login" in config,
                config['login'].get("enabled", False),
                "jwt" in config['login'])
        )
        return False


def setup(app: Flask, config: dict) -> None:
    """
    Factory for setting up everything needed for OIDC authentication, including

       * validating environment variables and config
       * setting up environment variables
       * registering login_required annotation
       * configure Flask app
       * set up current_user (user_loader_callback)

    This makes multiple requests to the issuer/identity provider!
    """
    # Get and validate necessary environment variables.
    issuer_url = _safe_getenv("OIDC_ISSUER_URL")
    client_secret = _safe_getenv('OIDC_CLIENT_SECRET')
    realm = _safe_getenv('OIDC_REALM')
    client_id = _safe_getenv('OIDC_CLIENTID')

    # JWT Setup
    _copy_jwt_vars_to_toplevel_config(app, config)
    oidc_config = _retrieve_oidc_config(issuer_url)
    app.config["JWT_PUBLIC_KEY"] = _retrieve_rsa_public_key(oidc_config)
    # Deactivate JWT CSRF since it is not working with external Identity Provider access tokens.
    # It is reimplemented by this module.
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    jwt_manager = JWTManager(app)

    # A a Login object to allow access to some information from the login_required decorator.
    app.oidc_login = Login(client_id, client_secret, realm, oidc_config)

    @jwt_manager.user_loader_callback_loader
    def user_loader_callback(identity: str) -> User:
        """
        This function returns a User Object if the flask_jwt_extended current_user is called
        :param identity: unused, since data of access token will be used here but its required
        :return: User
        """
        return User()


def _safe_getenv(key: str) -> str:
    value = os.environ[key]
    if value is None or len(value) == 0:
        raise ValueError("Environment variable '%s' is set to invalid value '%s'" % (key, value))
    return value


def _copy_jwt_vars_to_toplevel_config(flaskapp: Flask, config: dict) \
        -> None:
    """
    Flask_jwt_extended expect its configuration in the app.config object.
    Therefore we copy the config to the app object.
    """
    jwt_config_items = [
        "JWT_COOKIE_SECURE",
        "JWT_TOKEN_LOCATION",
        "JWT_ALGORITHM",
        "JWT_DECODE_AUDIENCE",
        "JWT_IDENTITY_CLAIM",
        "JWT_COOKIE_SECURE"
    ]
    for key in jwt_config_items:
        flaskapp.config[key] = config['login']['jwt'][key]


def _retrieve_rsa_public_key(oidc_config: dict) -> RSAPublicKey:
    """
    Do a sequence of requests to the identity provider to retrieve its public key
    :param issuer_url:
    :return:
    """
    jwks_uri = oidc_config["jwks_uri"]
    jwt = _retrieve_issuers_public_key_jwt(jwks_uri)
    return RSAAlgorithm.from_jwk(jwt)


def _retrieve_oidc_config(issuer_url: str, timeout_sec: int = 10) -> dict:
    config_url = "%s/.well-known/openid-configuration" % issuer_url
    for retry in range(4, -1, -1):
        try:
            response = requests.get(config_url)
            oidc_config = _validate_issuer_config_response(response)
            break

        except Exception as e:
            logger.warning(
                'Unable to JWKS endpoint from "%s". Retrying %d times' %
                (config_url, retry)
            )

            if not retry:
                logger.exception(
                    "Timeout! Could not receive JWKS endpoint from the identity provider! (%s)"
                    % config_url)
                raise e

            sleep(timeout_sec)

    return oidc_config


def _validate_issuer_config_response(response) -> dict:
    """
    This function validates that the config received from the Identity Provider has the correct
    format and contains all required data.
    :param config: Anything returned from .json().
    :return:
    """
    config = response.json()

    if not isinstance(config, dict):
        raise ValueError("Identity provider didn't respond with a dict but '%s': %s" %
                         (str(type(config)), response))

    required_values = [
        'authorization_endpoint',
        'token_endpoint',
        'jwks_uri'
    ]

    missing_values = [value for value in required_values if value not in config]
    if missing_values:
        raise ValueError("Missing fields in issuer response: %s" % ", ".join(missing_values))

    return config


def _retrieve_issuers_public_key_jwt(jwks_uri: str) -> str:
    logger.info("Extracting public certificate from issuer")
    try:
        response = requests.get(jwks_uri).json()
        public_key_jwt = json.dumps(response["keys"][0])

    except Exception as e:
        logger.exception("Could not connect to %s to receive the RSA public key!" % jwks_uri)
        logger.exception(e)
        raise e

    return public_key_jwt
