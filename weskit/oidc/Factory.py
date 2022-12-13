#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import json
import logging
from typing import Optional

from time import sleep

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from flask import Flask
from flask_jwt_extended import JWTManager
from jwt.algorithms import RSAAlgorithm

from weskit.classes.WESApp import WESApp
from weskit.oidc.Login import Login
from weskit.oidc.User import User
from weskit.utils import safe_getenv

logger = logging.getLogger(__name__)


def _is_login_enabled(config: dict) -> bool:
    """
    This function checks if all required configurations are set end enabled in the config file
    It returns true if the Login is correctly set up end enabled, otherwise false.

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
        logger.warning("has login block: {}, login is enabled: {}, has jwt: {}".
                       format("login" in config,
                              config['login'].get("enabled", False),
                              "jwt" in config['login']))
        return False


def setup(app: WESApp, config: dict) -> None:
    """
    Factory for setting up everything needed for OIDC authentication, including

       * validating environment variables and config
       * setting up environment variables
       * registering login_required annotation
       * configure Flask app
       * set up current_user (user_loader_callback)

    This makes multiple requests to the issuer/identity provider!
    """
    if not _is_login_enabled(config):
        app.is_login_enabled = False
        # flask-jwt-extension 4 needs some of these variables to be always set. Although the
        # documentation says for many of them that there is a default (e.g. for
        # JWT_TOKEN_LOCATION, JWT_HEADER_NAME, and JWT_HEADER_TYPE), we do get exceptions,
        # if the values are not set explicitly.
        _copy_jwt_vars_to_toplevel_config(app, config)
    else:
        app.is_login_enabled = True

        # Get and validate necessary environment variables.
        issuer_url = safe_getenv("OIDC_ISSUER_URL")
        client_secret = safe_getenv('OIDC_CLIENT_SECRET')
        realm = safe_getenv('OIDC_REALM')
        client_id = safe_getenv('OIDC_CLIENTID')

        # JWT Setup
        _copy_jwt_vars_to_toplevel_config(app, config)
        oidc_config = _retrieve_oidc_config(issuer_url)
        app.config["JWT_PUBLIC_KEY"] = _retrieve_rsa_public_key(oidc_config)
        # Deactivate JWT CSRF since it is not working with external Identity Provider access tokens.
        # It is reimplemented by this module.
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        jwt_manager = JWTManager(app)

        # A a Login object to allow access to some information from the login_required decorator.
        app.oidc_login = Login(client_id=client_id,
                               client_secret=client_secret,
                               realm=realm,
                               oidc_config=oidc_config)

        @jwt_manager.user_lookup_loader
        def user_loader_callback(jwt_headers: dict, jwt_payload: dict) -> User:
            """
            https://flask-jwt-extended.readthedocs.io/en/stable/api/#flask_jwt_extended.JWTManager.user_lookup_loader  # noqa

            This function returns a User object if the flask_jwt_extended current_user is called.

            :return: User
            """
            return User.from_jwt_payload(app, jwt_payload)


def _copy_jwt_vars_to_toplevel_config(flaskapp: Flask, config: dict) \
        -> None:
    """
    Flask_jwt_extended expect its configuration in the app.config object.
    Therefore, we copy the config to the app object.
    """
    jwt_config_items = [
        "JWT_COOKIE_SECURE",
        "JWT_TOKEN_LOCATION",
        "JWT_HEADER_NAME",
        "JWT_HEADER_TYPE",
        "JWT_ALGORITHM",
        "JWT_DECODE_AUDIENCE",
        "JWT_IDENTITY_CLAIM",
        "JWT_COOKIE_SECURE",
        "userinfo_validation_claim",
        "userinfo_validation_value"
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
    oidc_config: Optional[dict] = None
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

    if oidc_config is None:
        raise RuntimeError("Could not retrieve OIDC configuration")
    else:
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
