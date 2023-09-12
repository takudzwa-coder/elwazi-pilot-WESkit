#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import os
import sys
from logging.config import dictConfig
from pathlib import Path
from typing import cast

import yaml
from celery import Celery
from flask_cors import CORS

from weskit.api.RunRequestValidator import RunRequestValidator
from weskit.api.wes import bp as wes_bp
from weskit.classes.Database import Database
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.ErrorCodes import ErrorCodes
from weskit.classes.Manager import Manager
from weskit.classes.PathContext import PathContext
from weskit.api.ServiceInfo import ServiceInfo
from weskit.classes.WESApp import WESApp
from weskit.classes.WorkflowEngineFactory import WorkflowEngineFactory
from weskit.oidc import Factory as OIDCFactory
from weskit.utils import create_validator

logger = logging.getLogger(__name__)


def read_swagger():
    """Read the swagger file."""
    # This is hardcoded, because if it is changed, probably also quite some
    # code needs to be changed.
    swagger_file = "weskit/api/workflow_execution_service_1.0.0.yaml"
    with open(swagger_file, "r") as yaml_file:
        swagger = yaml.safe_load(yaml_file)

    return swagger


def create_database(database_url=None) -> Database:
    logger.info(f"Process ID (create_database) = {os.getpid()}")

    if database_url is None:
        database_url = os.getenv("WESKIT_DATABASE_URL")
    logger.info("Connecting to %s" % database_url)
    return Database(database_url, "WES")


def create_app(celery: Celery,
               database: Database) -> WESApp:
    logger.info(f"Process ID (create_app) = {os.getpid()}")

    if os.getenv("WESKIT_CONFIG") is not None:
        config_file = Path(cast(str, os.getenv("WESKIT_CONFIG")))
    else:
        raise ValueError("Cannot start WESkit: Environment variable WESKIT_CONFIG is undefined")

    log_config_file = Path(os.getenv(
        "WESKIT_LOG_CONFIG",
        os.path.join("config", "log-config.yaml"))).absolute()

    validation_config_file = Path(os.getenv(
        "WESKIT_VALIDATION_CONFIG",
        os.path.join("config", "validation.yaml"))).absolute()

    workflows_base_dir = Path(os.getenv(
        "WESKIT_WORKFLOWS",
        os.path.join(os.getcwd(), "workflows"))).absolute()

    weskit_data = Path(os.getenv("WESKIT_DATA", "./tmp")).absolute()

    request_validation_config = \
        os.path.join("config", "request-validation.yaml")

    with open(log_config_file, "r") as yaml_file:
        log_config = yaml.safe_load(yaml_file)
        dictConfig(log_config)
        logger.info("Read log config from " + str(log_config_file))

    with open(config_file, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        logger.info("Read config from " + str(config_file))

    with open(validation_config_file, "r") as yaml_file:
        validation = yaml.safe_load(yaml_file)
        logger.debug("Read validation specification from " +
                     str(validation_config_file))

    with open(request_validation_config, "r") as yaml_file:
        request_validation = yaml.safe_load(yaml_file)

    # Validate configuration YAML.
    validation_result = create_validator(validation)(config)
    if isinstance(validation_result, list):
        logger.error(f"Could not validate '{config_file}': %s" % validation_result)
        sys.exit(ErrorCodes.CONFIGURATION_ERROR.value)
    else:
        # The validation result contains the normalized config (with default values set).
        config = validation_result

    container_context = PathContext(data_dir=weskit_data,
                                    workflows_dir=workflows_base_dir)

    executor_type = EngineExecutorType.from_string(config["executor"]["type"])
    if executor_type.needs_login_credentials:
        executor_context = PathContext(data_dir=config["executor"]["remote_data_dir"],
                                       workflows_dir=config["executor"]["remote_workflows_dir"])
    else:
        executor_context = container_context

    # Insert the "celery" section from the configuration file into the Celery config.
    celery.conf.update(**config.get("celery", {}))
    manager = \
        Manager(celery_app=celery,
                database=database,
                config=config,
                workflow_engines=WorkflowEngineFactory.
                create(config["workflow_engines"]),
                weskit_context=container_context,
                executor_context=executor_context,
                require_workdir_tag=config["require_workdir_tag"])

    service_info = ServiceInfo(config["static_service_info"],
                               config["workflow_engines"],
                               read_swagger(),
                               database)

    # Create validators for each of the request types in the
    # request-validation.yaml. These are used in the API-calls to validate
    # the input.
    request_validators = {
        "run_request": RunRequestValidator(create_validator(
            request_validation["run_request"]),
            service_info.workflow_engine_versions_dict(),
            data_dir=weskit_data,
            require_workdir_tag=manager.require_workdir_tag)
    }

    app = WESApp(manager=manager,
                 service_info=service_info,
                 request_validators=request_validators,
                 log_config=log_config,
                 logger=logger)
    print(app.manager)

    app.register_blueprint(wes_bp)

    # Enable CORS headers for all origins, if enabled
    if config["cors"]["enabled"]:
        CORS(app)

    OIDCFactory.setup(app, config)

    return app
