import pytest
import os, yaml, logging
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.wesnake import create_app
from pymongo import MongoClient
from logging.config import dictConfig


@pytest.fixture(scope="function")
def test_app(test_config, validation, config_validation, service_info_validation, static_service_info, log_config,
             info_logger, error_logger, swagger, database_connection):
    app = create_app(test_config, validation, config_validation, service_info_validation, static_service_info,
                     log_config, info_logger, error_logger, swagger, database_connection)
    app.app.testing = True
    with app.app.test_client() as testing_client:
        ctx = app.app.app_context()
        ctx.push()
        yield testing_client


@pytest.fixture(scope="function")
def test_config():
    with open("config.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="function")
def validation():
    with open("validation.yaml", "r") as ff:
        validation = yaml.load(ff, Loader=yaml.FullLoader)
    yield validation


@pytest.fixture(scope="function")
def config_validation(validation):
    config_validation = validation["config_validation"]["schema"]
    yield config_validation


@pytest.fixture(scope="function")
def service_info_validation(validation):
    service_info_validation = validation["service_info_validation"]["schema"]
    yield service_info_validation


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
        static_service_info = yaml.load(ff, Loader=yaml.FullLoader)
    yield static_service_info


@pytest.fixture(scope="function")
def service_info(static_service_info, swagger, database_connection):
    yield ServiceInfo(static_service_info, swagger, database_connection)


@pytest.fixture(scope="function")
def log_config():
    with open("log_config.yaml", "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield log_config


@pytest.fixture(scope="function")
def info_logger(log_config):
    dictConfig(log_config)
    root_logger = logging.getLogger()
    yield root_logger


@pytest.fixture(scope="function")
def error_logger(log_config):
    dictConfig(log_config)
    logger_other = list(log_config["loggers"])
    other_logger = logging.getLogger(logger_other[0])
    yield other_logger


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("ga4gh/wes/20191217_workflow_execution_service.swagger.yaml", "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger
