#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import os
from pathlib import Path

import yaml

from weskit.classes.Database import Database
from weskit.classes.PathContext import PathContext

logger = logging.getLogger(__name__)


def weskit_data_dir() -> Path:
    return Path(os.getenv("WESKIT_DATA", "./tmp")).absolute()


def workflows_base_dir() -> Path:
    return Path(os.getenv("WESKIT_WORKFLOWS", os.path.join(os.getcwd(), "workflows"))).absolute()


def container_context() -> PathContext:
    return PathContext(data_dir=weskit_data_dir(),
                       workflows_dir=workflows_base_dir())


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
