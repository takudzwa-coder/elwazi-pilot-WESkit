#!/usr/bin/env python3

import argparse
import connexion
import yaml
import sys
import logging
import os
import time
import random
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.ErrorCodes import ErrorCodes
from ga4gh.wes.celery_utils import init_celery
from ga4gh.wes import celery


def create_app(config, validation, log_config, logger, database):

    swagger_file = "workflow_execution_service_1.0.0.yaml"
    app = connexion.App(__name__, specification_dir="swagger/")
    app.add_api(swagger_file)

    swagger_path = app.specification_dir / swagger_file
    with open(swagger_path, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

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


# TODO use config for db init
def create_database(config):
    return Database(MongoClient("database", 27017), "WES")



def main():
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--log_config", type=str, required=False,
                        default=os.path.join(sys.prefix,
                                             "config",
                                             "log-config.yaml"))
    parser.add_argument("--validation", type=str, required=False,
                        default=os.path.join(sys.prefix,
                                             "config",
                                             "validation.yaml"))
    args = parser.parse_args()

    with open(args.config, "r") as yaml_file:
        config = yaml.load(yaml_file, Loader=yaml.FullLoader)

    with open(args.validation, "r") as yaml_file:
        validation = yaml.load(yaml_file, Loader=yaml.FullLoader)

    with open(args.log_config, "r") as yaml_file:
        log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
        dictConfig(log_config)
        logger = logging.getLogger("default")

    app = create_app(config, validation, log_config,
                     logger, create_database(config))

    with app.app.app_context():
        from ga4gh.wes.routes import longtask, taskstatus
    
    init_celery(celery, app.app)


    app.run(port="4080", host="0.0.0.0", debug=True)
