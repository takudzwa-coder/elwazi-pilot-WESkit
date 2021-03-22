#!/usr/bin/env python3
from typing import Optional

import yaml
import sys
import logging
import os

from celery import Celery
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from flask import Flask, current_app

from weskit.classes.Database import Database
from weskit.classes.RunRequestValidator import RunRequestValidator
from weskit.classes.WorkflowEngine import WorkflowEngineFactory
from flask_jwt_extended import JWTManager
from weskit.classes.Manager import Manager
from weskit.classes.ServiceInfo import ServiceInfo
from weskit.classes.ErrorCodes import ErrorCodes


class WESApp(Flask):
    """We make a subclass of Flask that takes the important app-global
    (~thread local) resources.
    Compare https://stackoverflow.com/a/21845744/8784544"""

    def __init__(self,
                 manager: Manager,
                 service_info: ServiceInfo,
                 *args, **kwargs):
        super().__init__(__name__, *args, **kwargs)
        setattr(self, 'manager', manager)
        setattr(self, 'service_info', service_info)


def create_celery(broker_url=None,
                  backend_url=None):
    if broker_url is None:
        broker_url = os.environ.get("BROKER_URL")
    if backend_url is None:
        broker_url = os.environ.get("RESULT_BACKEND")
    celery = Celery(
        app="WESkit",
        broker=broker_url,
        backend=backend_url
    )
    celery_config = dict()
    celery_config["broker_url"] = broker_url
    celery_config["result_backend"] = backend_url
    celery.conf.update(celery_config)
    return celery


def read_swagger():
    """Read the swagger file."""
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "weskit/api/workflow_execution_service_1.0.0.yaml"
    with open(swagger_file, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return swagger


def create_database(database_url=None):
    if database_url is None:
        os.getenv("WESKIT_DATABASE_URL")
    return Database(MongoClient(database_url), "WES")


def create_validator(schema):
    """Return a validator function that can be provided a data structure to
    be validated. The validator is returned as second argument."""
    def _validate(target) -> Optional[str]:
        validator = Validator()
        result = validator.validate(target, schema)
        if result:
            return None
        else:
            return validator.errors
    return _validate


def create_app(celery: Celery, database: Database) -> Flask:
    default_config = os.getenv("WESKIT_CONFIG", None)
    default_log_config = os.getenv(
        "WESKIT_LOG_CONFIG",
        os.path.join("config", "log-config.yaml"))

    default_validation_config = os.getenv(
        "WESKIT_VALIDATION_CONFIG",
        os.path.join("config", "validation.yaml"))

    workflows_base_dir = os.getenv(
        "WESKIT_WORKFLOWS",
        os.path.join(os.getcwd(), "workflows"))

    weskit_data = os.getenv("WESKIT_DATA", "./tmp")

    request_validation_config = \
        os.path.join("config", "request-validation.yaml")

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

    with open(request_validation_config, "r") as yaml_file:
        request_validation = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Validate configuration YAML.
    config_errors = create_validator(validation)(config)
    if config_errors:
        logger.error("Could not validate config.yaml: {}".
                     format(config_errors))
        sys.exit(ErrorCodes.CONFIGURATION_ERROR)

    manager = \
        Manager(celery_app=celery,
                database=database,
                workflow_engines=WorkflowEngineFactory.
                workflow_engine_index(config
                                      ["static_service_info"]
                                      ["default_workflow_engine_parameters"]),
                workflows_base_dir=workflows_base_dir,
                data_dir=weskit_data)

    service_info = ServiceInfo(config["static_service_info"],
                               read_swagger(),
                               database)

    app = WESApp(manager, service_info)

    # Create validators for each of the request types in the
    # request-validation.yaml. These are used in the API-calls to validate
    # the input.
    app.request_validators = {
        "run_request": RunRequestValidator(create_validator(
            request_validation["run_request"]))
    }

    app.log_config = log_config
    app.logger = logger


    from weskit.api.wes import bp as wes_bp
    app.register_blueprint(wes_bp)

    ######################################
    #              Init Login            #
    ######################################

    # Enable Login by Default
    app.config["JWT_ENABLED"] = True

    # check if JWT auth is enabled in config
    if "jwt" in config and config["jwt"]["enabled"]:
        logger.info("User Authentication: ENABLED")

        ############################################
        #  config that would require code changes  #
        ############################################

        # Configure application to store JWTs in cookies
        app.config['JWT_TOKEN_LOCATION'] = ['cookies']

        # Set the cookie paths, so that you are only sending your access token
        # cookie to the access endpoints, and only sending your refresh token
        # to the refresh endpoint. Technically this is optional, but it is in
        # your best interest to not send additional cookies in the request if
        # they aren't needed.
        app.config['JWT_ACCESS_COOKIE_PATH'] = '/ga4gh/wes/'
        app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh'

        ############################################
        # Load config from config file            #
        ############################################
        for key, value in config["jwt"].items():
            app.config[key] = value

        jwt = JWTManager(app)

        from weskit.login import LoginBlueprint as login_bp
        app.register_blueprint(login_bp.login)

        ############################################
        #  Initialize local Config file            #
        ############################################

        if config["localAuth"]["enabled"]:
            logger.info("Initialize Local Auth")
            from weskit.login.auth.Local import Local as localAuth
            logger.info(
                "Using UserManagementFile %s!" %
                (config["localAuth"]["yamlPath"])
            )

            loginfile = config["localAuth"]["yamlPath"]

            app.authObject = localAuth(
                loginfile,
                'local',
                logger=app.logger)

    else:
        app.config["JWT_ENABLED"] = False
        logger.info(
            "User Authentication: DISABLED - "
            "'jwt' not present in WESKIT config!"
        )

    ####################################################################
    #               Overwrite JWT default fuctions                     #
    #  This allows the login to deal with objects instead of strings   #
    ####################################################################
    #  vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv  #

    # Create a function that will be called whenever create_access_token
    # is used. It will take whatever object is passed into the
    # create_access_token method, and lets us define what custom claims
    # should be added to the access token.

    @jwt.user_claims_loader
    def add_claims_to_access_token(user):
        if len(user.roles):
            return {'roles': user.roles}
        return None

    # Create a function that will be called whenever create_access_token
    # is used. It will take whatever object is passed into the
    # create_access_token method, and lets us define what the identity
    # of the access token should be.
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return {'username': user.username, 'authType': user.authType}

    # This function is called whenever a protected endpoint is accessed,
    # and must return an object based on the tokens identity.
    # This is called after the token is verified, so you can use
    # get_jwt_claims() in here if desired. Note that this needs to
    # return None if the user could not be loaded for any reason,
    # such as not being found in the underlying data store

    @jwt.user_loader_callback_loader
    def user_loader_callback(identity):
        return current_app.authObject.get(identity['username'])

    ####################################################################
    #               END overwrite  JWT default fuctions                #
    #  This allows the login to deal with objects instead of strings   #
    ####################################################################

    return app
