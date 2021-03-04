#!/usr/bin/env python3

import yaml
import sys
import logging
import os
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from flask import Flask

from weskit.login import Login


def read_swagger():
    '''Read the swagger file.'''
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "weskit/api/workflow_execution_service_1.0.0.yaml"
    with open(swagger_file, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return swagger


def create_database():
    from weskit.classes.Database import Database

    DATABASE_URL = os.getenv("WESKIT_DATABASE_URL")
    return Database(MongoClient(DATABASE_URL), "WES")


def create_app():

    from weskit.classes.Manager import Manager
    from weskit.classes.ServiceInfo import ServiceInfo
    from weskit.classes.ErrorCodes import ErrorCodes

    default_config = os.getenv("WESKIT_CONFIG", None)
    default_log_config = os.getenv(
        "WESKIT_LOG_CONFIG",
        os.path.join("config", "log-config.yaml"))

    default_validation_config = os.getenv(
        "WESKIT_VALIDATION_CONFIG",
        os.path.join("config", "validation.yaml"))

    with open(default_log_config, "r") as yaml_file:
        log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
        dictConfig(log_config)
        logger = logging.getLogger("default")
        logger.info("Read log config from " + default_log_config)

    with open(default_config, "r") as yaml_file:
        config = yaml.load(yaml_file, Loader=yaml.FullLoader)
        logger.info("Read config from " + default_config)

    with open(default_validation_config, "r") as yaml_file:
        validation = yaml.load(yaml_file, Loader=yaml.FullLoader)
        logger.debug("Read validation specification from " +
                     default_validation_config)

    # Validate configuration YAML.
    validator = Validator()
    config_validation = validator.validate(config, validation)
    if config_validation is not True:
        logger.error("Could not validate config.yaml: {}".
                     format(validator.errors))
        sys.exit(ErrorCodes.CONFIGURATION_ERROR)

    swagger = read_swagger()

    app = Flask(__name__)

    # Global objects and information.
    app.validation = validation
    app.database = create_database()

    app.manager = Manager(config=config,
                          datadir=os.getenv("WESKIT_DATA", "./tmp"))
    app.service_info = ServiceInfo(config["static_service_info"],
                                   swagger, app.database)
    app.log_config = log_config
    app.logger = logger

    from weskit.api.wes import bp as wes_bp
    app.register_blueprint(wes_bp)

    ######################################
    #              Init Login            #
    ######################################
    app.config["OIDC_ISSUER_URL"] = "http://keycloak:8080/auth/realms/WESkit"
    app.config["OIDC_REALM"] = "WESkit"
    app.config["OIDC_CLIENTID"] = "WESkit"
    app.config["OIDC_CIENT_SECRET"] = "a8086bcc-44f3-40f9-9e15-fd5c3c98ab24"

    app.config["OIDC_FLASKHOST"] = "https://localhost:5000"

    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    app.config["JWT_ALGORITHM"] = "RS256"
    app.config["JWT_DECODE_AUDIENCE"] = "account"
    app.config["JWT_IDENTITY_CLAIM"] = "sub"

    # Only allow JWT cookies to be sent over https. In production, this
    # should likely be True
    app.config['JWT_COOKIE_SECURE'] = True

    # Set the cookie paths, so that you are only sending your access token
    # cookie to the access endpoints, and only sending your refresh token
    # to the refresh endpoint. Technically this is optional but it is in
    # your best interest to not send additional cookies in the request if
    # they aren't needed.
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/'

    # Enable csrf double submit protection. See this for a thorough
    # explanation: http://www.redotheweb.com/2015/11/09/api-security.html

    Login.odicLogin(app)

    return app
