#!/usr/bin/env python3

import yaml
import sys
import logging
import os
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from flask import Flask


def read_swagger():
    '''Read the swagger file.'''
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "wesnake/api/workflow_execution_service_1.0.0.yaml"
    with open(swagger_file, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return swagger


def create_database():
    from wesnake.classes.Database import Database

    DATABASE_URL = os.getenv("WESNAKE_DATABASE_URL")
    return Database(MongoClient(DATABASE_URL), "WES")


def create_app():

    from wesnake.classes.Snakemake import Snakemake
    from wesnake.classes.ServiceInfo import ServiceInfo
    from wesnake.classes.ErrorCodes import ErrorCodes

    default_config = os.getenv("WESNAKE_CONFIG", None)
    default_log_config = os.getenv(
        "WESNAKE_LOG_CONFIG",
        os.path.join("config", "log-config.yaml"))

    default_validation_config = os.getenv(
        "WESNAKE_VALIDATION_CONFIG",
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

    app.snakemake = Snakemake(config)
    app.service_info = ServiceInfo(config["static_service_info"],
                                   swagger, app.database)
    app.log_config = log_config
    app.logger = logger

    from wesnake.api.wes import bp as wes_bp
    app.register_blueprint(wes_bp)

    return app
