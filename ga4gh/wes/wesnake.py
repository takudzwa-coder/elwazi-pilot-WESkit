#!/usr/bin/env python3

import argparse
import connexion
import yaml
import sys
import logging
import os
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.ErrorCodes import ErrorCodes
import ga4gh.wes.routes

def read_swagger():
    '''Read the swagger file'''
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "workflow_execution_service_1.0.0.yaml"
    app = connexion.App(__name__, specification_dir="swagger/")
    app.add_api(swagger_file)

    swagger_path = app.specification_dir / swagger_file
    with open(swagger_path, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return swagger


def create_database(config):
    return Database(MongoClient(config["mongo_server"]["host"],
                                config["mongo_server"]["port"]),
                    "WES")


# This function takes parameters to simplify unit testing. Otherwise
# environment or configuration value processing is done in this
# function.
# Setup is located here to allow `flask run` to be used in the
# container.
def create_app(config = None,
               validation = None,
               log_config = None,
               logger = None,
               database = None):

    # Use the environment variables as default values.
    default_log_config = os.getenv("WESNAKE_CONFIG",
                                   os.path.join(sys.prefix, "config",
                                                "log-config.yaml"))

    default_validation_config = os.getenv("WESNAKE_VALIDATION_CONFIG",
                                          os.path.join(sys.prefix, "config",
                                                       "validation.yaml"))

    parser = argparse.ArgumentParser(description="WESnake")

    if config is None:
        if "WESNAKE_CONFIG" in os.environ:
            parser.add_argument("--config", type=str, required=False,
                                default=os.environ.get("WESNAKE_CONFIG"))
        else:
            # When there is no environment variable, then a value is required.
            parser.add_argument("--config", type=str, required=True)

        # These remain optional as command-line parameters.
        parser.add_argument("--log_config", type=str, required=False,
                            default=default_log_config)
        parser.add_argument("--validation", type=str, required=False,
                            default=default_validation_config)

        args = parser.parse_args()

        with open(args.config, "r") as yaml_file:
            config = yaml.load(yaml_file, Loader=yaml.FullLoader)

        with open(args.validation, "r") as yaml_file:
            validation = yaml.load(yaml_file, Loader=yaml.FullLoader)

        with open(args.log_config, "r") as yaml_file:
            log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
            dictConfig(log_config)
            logger = logging.getLogger("default")

        if database is None:
            database = create_database(config)

    swagger = read_swagger()

    # Validate configuration YAML.
    validator = Validator()
    config_validation = validator.validate(config, validation)
    if config_validation is not True:
        logger.error("Could not validate config.yaml: {}".
                     format(validator.errors))
        sys.exit(ErrorCodes.CONFIGURATION_ERROR)

    # Use the conventional app.config attribute
    app.config = config

    # Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]

    # Global objects and information.
    app.app.validation = validation
    app.app.database = database
    app.app.snakemake = Snakemake()
    app.app.service_info = ServiceInfo(config["static_service_info"],
                                       swagger, database)
    app.app.log_config = log_config
    app.app.logger = logger

    return app


def main():

    app = create_app()

    # Import of two routes for celery testing; TODO: remove later
    app.app.register_blueprint(ga4gh.wes.routes.simple_page)

    app.run(port=app.config["wes_server"]["port"],
            host=app.config["wes_server"]["host"],
            debug=app.debug)
