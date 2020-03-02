#!/usr/bin/env python3

import argparse
import connexion
import yaml
from pymongo import MongoClient
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake

def create_app(config):

    # Set app
    app = connexion.App(__name__)
    app.add_api("20191217_workflow_execution_service.swagger.yaml")

    ## Replace Connexion app settings
    app.host = config["wes_server"]["host"]
    app.port = config["wes_server"]["port"]
    app.debug = config["debug"]

    ## Replace Flask app settings
    app.app.config['DEBUG'] = app.debug
    app.app.config['ENV'] = "development"
    app.app.config['TESTING'] = False

    ## Setup database connection
    app.app.database = Database(MongoClient(), "WES")

    ## Setup snakemake executer
    app.app.snakemake = Snakemake()
    
    return app

import sys
def main():
    print("test", file=sys.stderr)
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    with open(args.config, "r") as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    
    app = create_app(config)
    app.run()
