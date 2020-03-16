#!/usr/bin/env python3

import argparse, connexion, yaml, sys
from pymongo import MongoClient
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo


def create_app(config, service_info, log_config, swagger, database):

    # Set app
    app = connexion.App(__name__)
    app.add_api("20191217_workflow_execution_service.swagger.yaml")

    # Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]
    app.debug = config["debug"]

    # Replace Flask app settings
    app.app.config['DEBUG'] = app.debug
    app.app.config['ENV'] = "development"
    app.app.config['TESTING'] = False

    # Setup database connection
    app.app.database = database

    # Setup snakemake executer
    app.app.snakemake = Snakemake()
    
    # Setup service_info
    app.app.service_info = ServiceInfo(service_info, swagger, database)

    # Setup log_config
    app.app.log_config = log_config

    # Setup swagger
    app.app.swagger = swagger
    
    return app


def main():
    print("test", file=sys.stderr)
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    with open(args.config, "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)

    parser_info = argparse.ArgumentParser(description="ServiceInfo")
    parser.add_argument("--config", type=str, required=True)
    args_info = parser_info.parse_args()
    with open(args_info.config, "r") as ff:
        service_info = yaml.load(ff, Loader=yaml.FullLoader)

    parser_log = argparse.ArgumentParser(description="Logging")
    parser.add_argument("--config", type=str, required=True)
    args_log = parser_log.parse_args()
    with open(args_log.config, "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)

    parser_swagger = argparse.ArgumentParser(description="Swagger")
    parser.add_argument("--config", type=str, required=True)
    args_swagger = parser_swagger.parse_args()
    with open(args_swagger.config, "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    
    app = create_app(config, service_info, log_config, swagger, Database(MongoClient(), "WES"))
    app.run()
