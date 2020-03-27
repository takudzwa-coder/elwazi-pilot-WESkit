#!/usr/bin/env python3

import argparse, connexion, yaml, sys, logging, cerberus
import ga4gh.wes.validation as validate
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo


def create_app(config, validation, config_validation, service_info_validation, static_service_info, log_config,
               info_logger, error_logger, swagger, database):

    # Set app
    app = connexion.App(__name__)
    app.add_api("20191217_workflow_execution_service.swagger.yaml")

    validator = validate.validate_config(config, config_validation)
    if validator is not True:
        error_logger.error("schema not valid")
        raise cerberus.schema.SchemaError

    # Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]
    app.debug = config["debug"]

    # Replace Flask app settings
    app.app.config['DEBUG'] = app.debug
    app.app.config['ENV'] = "development"
    app.app.config['TESTING'] = False

    app.app.validation = validation

    app.app.database = database

    app.app.snakemake = Snakemake()

    app.app.service_info = ServiceInfo(static_service_info, swagger, database)

    app.app.log_config = log_config

    # Setup info_logger for only writing the lof-info into the log-file
    app.app.info_logger = logging.getLogger()

    # Setup error_logger for writing the log-error into the log-file and at the console
    logger_other = list(log_config["loggers"])
    app.app.error_logger = logging.getLogger(logger_other[0])

    app.app.swagger = swagger
    
    return app


def main():
    print("test", file=sys.stderr)
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    with open(args.config, "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)

    parser_validation = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--validation", type=str, required=True)
    args_validation = parser_validation.parse_args()
    with open(args_validation.config, "r") as ff:
        validation = yaml.load(ff, Loader=yaml.FullLoader)
        config_validation = validation["config_validation"]["schema"]
        service_info_validation = validation["service_info_validation"]["schema"]

    parser_test_config = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--test_config", type=str, required=True)
    args_test_config = parser_test_config.parse_args()
    with open(args_test_config.config, "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)

    parser_info = argparse.ArgumentParser(description="ServiceInfo")
    parser.add_argument("--service_info", type=str, required=True)
    args_info = parser_info.parse_args()
    with open(args_info.config, "r") as ff:
        static_service_info = yaml.load(ff, Loader=yaml.FullLoader)

    parser_log = argparse.ArgumentParser(description="Logging")
    parser.add_argument("--log_config", type=str, required=True)
    args_log = parser_log.parse_args()
    with open(args_log.config, "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
        dictConfig(log_config)
        info_logger = logging.getLogger()
        error_logger = logging.getLogger(log_config["loggers"]["other"])

    parser_swagger = argparse.ArgumentParser(description="Swagger")
    parser.add_argument("--swagger", type=str, required=True)
    args_swagger = parser_swagger.parse_args()
    with open(args_swagger.config, "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)

    app = create_app(config, validation, config_validation, service_info_validation, static_service_info, log_config,
                     info_logger, error_logger, swagger, Database(MongoClient(), "WES"))
    app.run()
