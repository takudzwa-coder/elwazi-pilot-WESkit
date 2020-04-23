#!/usr/bin/env python3

import argparse, connexion, yaml, sys, logging
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.ErrorCodes import ErrorCodes


def create_app(config, validation, static_service_info, log_config, logger, swagger, database):

    app = connexion.App(__name__)
    app.add_api("20191217_workflow_execution_service.swagger.yaml")

    # Validate configuration YAML.
    validator = Validator()
    config_validation = validator.validate(config, validation["config"])
    if config_validation is not True:
        logger.error("Could not validate config.yaml: {}".format(validator.errors))
        sys.exit(ErrorCodes.CONFIGURATION_ERROR)

    # Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]
    app.debug = config["debug"]

    # Replace Flask app settings
    app.app.config['DEBUG'] = app.debug
    app.app.config['ENV'] = "development"
    app.app.config['TESTING'] = False

    # Global objects and information.
    app.app.validation = validation
    app.app.database = database
    app.app.snakemake = Snakemake()
    app.app.service_info = ServiceInfo(config["static_service_info"], swagger, database)
    app.app.log_config = log_config
    app.app.logger = logger
    app.app.swagger = swagger
    
    return app


def main():
    print("test", file=sys.stderr)
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--log_config", type=str, required=True)
    parser.add_argument("--swagger", type=str, required=True)
    parser.add_argument("--validation", type=str, required=True)
    args = parser.parse_args()

    with open(args.config, "r") as yaml_file:
        config = yaml.load(yaml_file, Loader=yaml.FullLoader)

    with open(args.validation, "r") as yaml_file:
        validation = yaml.load(yaml_file, Loader=yaml.FullLoader)

    with open(args.log_config, "r") as yaml_file:
        log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
        dictConfig(log_config)
        logger = logging.getLogger("default")

    with open(args.swagger, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    app = create_app(config, validation, log_config,
                     logger, swagger, Database(MongoClient(), "WES"))
    app.run()
