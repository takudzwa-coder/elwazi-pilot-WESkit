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
from flask import Flask

from weskit.oidc.Login import Login
from weskit.oidc import Factory as OIDCFactory
from weskit.classes.Database import Database
from weskit.classes.RunRequestValidator import RunRequestValidator
from weskit.classes.WorkflowEngine import WorkflowEngineFactory
from weskit.classes.Manager import Manager
from weskit.classes.ServiceInfo import ServiceInfo
from weskit.classes.ErrorCodes import ErrorCodes


logger = logging.getLogger(__name__)


class WESApp(Flask):
    """We make a subclass of Flask that takes the important app-global
    (~thread local) resources.
    Compare https://stackoverflow.com/a/21845744/8784544"""

    def __init__(self,
                 manager: Manager,
                 service_info: ServiceInfo,
                 request_validators: dict,
                 oidc_login: Optional[Login] = None,
                 *args, **kwargs):
        super().__init__(__name__, *args, **kwargs)
        setattr(self, 'manager', manager)
        setattr(self, 'service_info', service_info)
        setattr(self, 'request_validators', request_validators)
        setattr(self, 'oidc_login', oidc_login)


def create_celery(broker_url=None,
                  backend_url=None):
    if broker_url is None:
        broker_url = os.environ.get("BROKER_URL")
    if backend_url is None:
        backend_url = os.environ.get("RESULT_BACKEND")
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
        database_url = os.getenv("WESKIT_DATABASE_URL")
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
                data_dir=weskit_data,
                require_workdir_tag=config["require_workdir_tag"])

    service_info = ServiceInfo(config["static_service_info"],
                               read_swagger(),
                               database)

    # Create validators for each of the request types in the
    # request-validation.yaml. These are used in the API-calls to validate
    # the input.
    request_validators = {
        "run_request": RunRequestValidator(create_validator(
            request_validation["run_request"]))
    }

    app = WESApp(manager,
                 service_info,
                 request_validators)

    app.log_config = log_config
    app.logger = logger

    from weskit.api.wes import bp as wes_bp
    app.register_blueprint(wes_bp)

    if OIDCFactory.is_login_enabled(config):
        OIDCFactory.setup(app, config)

    return app
