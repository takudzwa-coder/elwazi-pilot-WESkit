#!/usr/bin/env python3

import argparse
import connexion
import yaml

# load arguments


def create_app(config):
    print("create app")
    # set app
    app = connexion.App(__name__)
    app.add_api("20191217_workflow_execution_service.swagger.yaml")

    ## Replace Connexion app settings
    app.host = config["server"]["host"]
    app.port = config["server"]["port"]
    app.debug = config["server"]["debug"]

    ## Replace Flask app settings
    app.app.config['DEBUG'] = app.debug
    app.app.config['ENV'] = "development"
    app.app.config['TESTING'] = False


    #TODO setup database connection

    return(app)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WESnake")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    with open(args.config, "r") as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    
    app = create_app(config)
    app.run()