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
from ga4gh.wes.celery_utils import init_celery
from ga4gh.wes import celery


def create_connexion_app():
    '''Read the swagger file.'''
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "workflow_execution_service_1.0.0.yaml"
    app = connexion.App(__name__, specification_dir="swagger/")
    app.add_api(swagger_file)

    swagger_path = app.specification_dir / swagger_file
    with open(swagger_path, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return app, swagger


def create_database(config):
    return Database(MongoClient(config["mongo_server"]["host"],
                                config["mongo_server"]["port"]),
                    "WES")


def parse_cli(default_config, default_log_config, default_validation_config):
    '''Command-line options: Take all values from there, defaulting to
    ones from the environment or the static defaults. Note that if
    default_config is None, then the parameter is required as CLI parameter.'''
    parser = argparse.ArgumentParser(description="WESnake")

    if default_config is not None:
        parser.add_argument("--config", type=str, required=False,
                            default=default_config)
    else:
        # When there is no environment variable, then a value is required.
        parser.add_argument("--config", type=str, required=True)

    # These remain optional as command-line parameters.
    parser.add_argument("--log_config", type=str, required=False,
                        default=default_log_config)
    parser.add_argument("--validation", type=str, required=False,
                        default=default_validation_config)

    args = parser.parse_args()

    return {
        "config": args.config,
        "log_config": args.log_config,
        "validation": args.validation
    }


# This function takes parameters to simplify unit testing. Otherwise
# environment or configuration value processing is done in this
# function.
#
# All configuration-reading is located here to allow using `flask run`  with
# the primary aim to simplify development in the container. Note, however,
# that this currently fails with
#
#  FLASK_APP="ga4gh/wes/wesnake:create_app()" flask run
#
# Because connexion does not return a flask app.
#
def create_app(config=None,
               validation=None,
               log_config=None,
               logger=None,
               database=None,
               celery=None):
    '''
    If config is given, then it is expected that all paramters are provided.
    If config is not given, then all values are loaded from files are
    created from the configurations specified in there. If a command-line
    parameter is provided, then all values are expected to be provided via
    command line parameters but defaults are still taken from the environment.
    Otherwise configuraton file paths are taken from WESNAKE_CONFIG, and if
    provided WESNAKE_LOG_CONFIG and WESNAKE_VALIDATION_CONFIG.
    '''

    if config is None:
        # Use the environment variables as default values.

        # No static default here!
        default_config = os.getenv("WESNAKE_CONFIG", None)

        default_log_config = os.getenv(
            "WESNAKE_LOG_CONFIG",
            os.path.join(sys.prefix, "config",
                         "log-config.yaml"))

        default_validation_config = os.getenv(
            "WESNAKE_VALIDATION_CONFIG",
            os.path.join(sys.prefix, "config",
                         "validation.yaml"))

        if "--config" in sys.argv:
            args = parse_cli(default_config,
                             default_log_config,
                             default_validation_config)
        else:
            # No command-line options: Take all values from the environment.
            args = {
                "config": default_config,
                "log_config": default_log_config,
                "validation": default_validation_config
            }

        with open(args["log_config"], "r") as yaml_file:
            log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
            dictConfig(log_config)
            logger = logging.getLogger("default")
            logger.info("Read log config from " + args["log_config"])

        with open(args["config"], "r") as yaml_file:
            config = yaml.load(yaml_file, Loader=yaml.FullLoader)
            logger.info("Read config from " + args["config"])

        with open(args["validation"], "r") as yaml_file:
            validation = yaml.load(yaml_file, Loader=yaml.FullLoader)
            logger.debug("Read validation specification from " +
                         args["validation"])

        if database is None:
            database = create_database(config)

    # Validate configuration YAML.
    validator = Validator()
    config_validation = validator.validate(config, validation)
    if config_validation is not True:
        logger.error("Could not validate config.yaml: {}".
                     format(validator.errors))
        sys.exit(ErrorCodes.CONFIGURATION_ERROR)

    app, swagger = create_connexion_app()

    # Use the conventional app.config attribute
    app.config = config

    # Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]

    # Initialize celery
    init_celery(celery, app)

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
    print("Starting WESnake ...", file=sys.stderr)

    app = create_app(celery=celery)

    app.run(port=app.config["wes_server"]["port"],
            host=app.config["wes_server"]["host"],
            debug=app.debug)
