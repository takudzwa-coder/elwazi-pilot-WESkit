import logging
import os
from flask import Flask
from weskit.classes.ErrorCodes import ErrorCodes
from typing import Optional, Any

logger = logging.getLogger(__name__)


def isLoginEnabled(config: dict) -> bool:
    """
    This function checks if all required configurations are set end enabled in the config file
    It returns true if the Login is correctly set up end enabled, otherwise false

    :param config: configuration dict
    :return:
    """
    # Check if the Login System can be Initialized
    if (
            "login" in config and
            config['login'].get("enabled", False) and
            "jwt" in config['login']
    ):
        return True

    else:
        # Print Warning that LoginSystem is disabled via Config!

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


def validate_setup_login_config(flaskapp: Flask, oidcLoginObject, config: dict) -> None:
    """
    validate_store_login_config checks the login config via os.environ and configfile for
    completeness and stores the config in the oidcLoginObject and the flask app(JWT_config).

    If any value is missing the Server will be stopped by this function.

    :param flaskapp:
    :param oidcLoginObject:
    :param config:
    """
    try:
        # Flask_jwt_extended expect its configuration in the app.config object.
        # Therefore we copy the config to the app object.
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

        oidcLoginObject.issuer_url = os.environ["OIDC_ISSUER_URL"]

        oidcLoginObject.client_secret = os.environ['OIDC_CLIENT_SECRET']
        oidcLoginObject.realm = os.environ['OIDC_REALM']
        oidcLoginObject.client_id = os.environ['OIDC_CLIENTID']
    except KeyError as ke:
        environ = [
            "OIDC_ISSUER_URL",
            "OIDC_CLIENT_SECRET",
            "OIDC_REALM",
            "OIDC_CLIENTID"
        ]

        missing_config = {
            "Environment Variables": [key for key in environ if key not in os.environ.keys()],
            "Configfile jwt": [key for key in jwt_config_items if key not in config['login']['jwt']]
        }

        import yaml
        logger.exception(
            "OIDC Login Configuration Incomplete!\n"
            "MissingValues: \n\n"
            "%s\n_______________________" % yaml.dump(missing_config)
        )

        logger.exception(ke)
        exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)


def validate_received_config_or_stop(config: Any) -> Optional[dict]:
    """
    This function validates that the config received from the Identity Provider has the correct
    format and contains all required data.
    :param config:
    :return:
    """

    if not isinstance(config, dict):
        logger.exception(
            "The configuration received from Identity Provider does not have the expected"
            "type dict! The type is %s. The server will be stopped now!" % str(type(config))
        )
        exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)

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
        exit(ErrorCodes.LOGIN_CONFIGURATION_ERROR)

    return config
