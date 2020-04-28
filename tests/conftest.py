import pytest
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.wesnake import create_app
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from logging.config import dictConfig
import yaml

@pytest.fixture(scope="function")
def test_app(test_config, validation, static_service_info, log_config,
             logger, swagger, database_connection):
    app = create_app(test_config, validation, static_service_info,
                     log_config, logger, swagger, database_connection)
    app.app.testing = True
    with app.app.test_client() as testing_client:
        ctx = app.app.app_context()
        ctx.push()
        yield testing_client


@pytest.fixture(scope="function")
def test_config():
    # This uses a dedicated test configuration YAML.
    with open("tests/config.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="function")
def validation():
    # This uses the global validation YAML because YAML file structures should be identical in test and production.
    with open("validation.yaml", "r") as ff:
        validation = yaml.load(ff, Loader=yaml.FullLoader)
    yield validation

@pytest.fixture(scope="function")
def database_connection():
    container = MongoDbContainer('mongo:4.2.3')
    container.start()
    database = Database(MongoClient(container.get_connection_url()), "WES_Test")
    yield database
    database._db_runs().drop()


@pytest.fixture(scope="function")
def snakemake_executor():
    executor = Snakemake()
    yield executor


@pytest.fixture(scope="function")
def static_service_info(test_config):
    yield test_config["static_service_info"]


@pytest.fixture(scope="function")
def service_info(static_service_info, swagger, database_connection):
    yield ServiceInfo(static_service_info, swagger, database_connection)


@pytest.fixture(scope="function")
def log_config():
    # There is a special logger "tests" for test-associated logging.
    with open("log_config.yaml", "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield log_config


@pytest.fixture(scope="function")
def logger(log_config):
    dictConfig(log_config)
    yield logging.getLogger("test")


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("ga4gh/wes/20191217_workflow_execution_service.swagger.yaml", "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger
