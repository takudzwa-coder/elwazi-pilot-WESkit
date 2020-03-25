import pytest
import os, yaml, logging
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.wesnake import create_app
from pymongo import MongoClient
from logging.config import dictConfig


@pytest.fixture(scope="function")
def test_app(test_config, config_validation, static_service_info, service_info_validation, log_config, root_logger, other_logger, swagger, database_connection):
    app = create_app(test_config, config_validation, static_service_info, service_info_validation, log_config, root_logger, other_logger, swagger, database_connection)
    app.app.testing = True
    with app.app.test_client() as testing_client:
        ctx = app.app.app_context()
        ctx.push()
        yield testing_client


@pytest.fixture(scope="function")
def test_config():
    with open("tests/test_config.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="function")
def config_validation():
    with open("config_validation.yaml", "r") as ff:
        config_validation = yaml.load(ff, Loader=yaml.FullLoader)
    yield config_validation


@pytest.fixture(scope="function")
def database_connection():
    connection_url = os.environ["WESNAKE_TEST"]
    database = Database(MongoClient(connection_url), "WES_Test")
    yield database
    database._db_runs().drop()


@pytest.fixture(scope="function")
def snakemake_executor():
    executor = Snakemake()
    yield executor


@pytest.fixture(scope="function")
def static_service_info(database_connection):
    with open("service_info.yaml", "r") as ff:
        service_info = yaml.load(ff, Loader=yaml.FullLoader)
    yield service_info


@pytest.fixture(scope="function")
def service_info_validation():
    with open("service_info_validation.yaml", "r") as ff:
        service_info_validation = yaml.load(ff, Loader=yaml.FullLoader)
    yield service_info_validation


@pytest.fixture(scope="function")
def service_info(static_service_info, swagger, database_connection):
    executor = ServiceInfo(static_service_info, swagger, database_connection)
    yield executor


@pytest.fixture(scope="function")
def log_config():
    with open("log_config.yaml", "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield log_config


@pytest.fixture(scope="function")
def root_logger(log_config):
    dictConfig(log_config)
    root_logger = logging.getLogger()
    yield root_logger


@pytest.fixture(scope="function")
def other_logger(log_config):
    dictConfig(log_config)
    logger_other = list(log_config["loggers"])
    other_logger = logging.getLogger(logger_other[0])
    yield other_logger


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("ga4gh/wes/20191217_workflow_execution_service.swagger.yaml", "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger
