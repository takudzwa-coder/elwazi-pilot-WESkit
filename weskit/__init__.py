#!/usr/bin/env python3

import yaml
import sys
import logging
import os
from cerberus import Validator
from pymongo import MongoClient
from logging.config import dictConfig
from flask import Flask

from flask_jwt_extended import JWTManager
import weskit.login



def read_swagger():
    '''Read the swagger file.'''
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "weskit/api/workflow_execution_service_1.0.0.yaml"
    with open(swagger_file, "r") as yaml_file:
        swagger = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return swagger


def create_database():
    from weskit.classes.Database import Database

    DATABASE_URL = os.getenv("WESKIT_DATABASE_URL")
    return Database(MongoClient(DATABASE_URL), "WES")


def create_app():

    from weskit.classes.Snakemake import Snakemake
    from weskit.classes.ServiceInfo import ServiceInfo
    from weskit.classes.ErrorCodes import ErrorCodes

    default_config = os.getenv("WESKIT_CONFIG", None)
    default_log_config = os.getenv(
        "WESKIT_LOG_CONFIG",
        os.path.join("config", "log-config.yaml"))

    default_validation_config = os.getenv(
        "WESKIT_VALIDATION_CONFIG",
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

    app.snakemake = Snakemake(config=config,
                              datadir=os.getenv("WESKIT_DATA", "./tmp"))
    app.service_info = ServiceInfo(config["static_service_info"],
                                   swagger, app.database)
    app.log_config = log_config
    app.logger = logger
    
    from weskit.api.wes import bp as wes_bp
    app.register_blueprint(wes_bp)
    
    ######################################
    ##            Init Login            ##
    ######################################
    
    ############################################
    ## config that would require code changes ##
    ############################################
    
    # Configure application to store JWTs in cookies
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']

    # Set the cookie paths, so that you are only sending your access token
    # cookie to the access endpoints, and only sending your refresh token
    # to the refresh endpoint. Technically this is optional, but it is in
    # your best interest to not send additional cookies in the request if
    # they aren't needed.
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/ga4gh/wes/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh'


    ############################################
    ## Load config from config file           ##
    ############################################
    for key,value in config["jwt_config"].items():
        app.config[key]=value
    
    jwt = JWTManager(app)

    from weskit.login import LoginBlueprint as login_bp
    app.register_blueprint(login_bp.login)

    ####################################################################
    ##              Overwrite JWT default fuctions                    ##
    ## This allows the login to deal with objects instead of strings  ##
    ####################################################################
    ## vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv ##
    
    
    # Create a function that will be called whenever create_access_token
    # is used. It will take whatever object is passed into the
    # create_access_token method, and lets us define what custom claims
    # should be added to the access token.
    
    @jwt.user_claims_loader
    def add_claims_to_access_token(user):
        if len(user.roles):
            return {'roles': user.roles}
        return(None)
    
    
    # Create a function that will be called whenever create_access_token
    # is used. It will take whatever object is passed into the
    # create_access_token method, and lets us define what the identity
    # of the access token should be.
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return {'username':user.username,'authType':user.authType}
    
    
    # This function is called whenever a protected endpoint is accessed,
    # and must return an object based on the tokens identity.
    # This is called after the token is verified, so you can use
    # get_jwt_claims() in here if desired. Note that this needs to
    # return None if the user could not be loaded for any reason,
    # such as not being found in the underlying data store
    @jwt.user_loader_callback_loader
    def user_loader_callback(identity):
        return(login.authObjDict.get('local').get(identity['username']))
    
    ####################################################################
    ##              END overwrite  JWT default fuctions               ##
    ## This allows the login to deal with objects instead of strings  ##
    ####################################################################
    
    
    
    return app
