import pytest
import os, yaml
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from pymongo import MongoClient


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
def service_info(database_connection):
    with open("tests/service_info.yaml", "r") as ff:
        service_info = yaml.load(ff, Loader=yaml.FullLoader)
    yield service_info


@pytest.fixture(scope="function")
def service_info_executor(service_info, database_connection):
    executor = ServiceInfo(service_info, swagger, database_connection)
    yield executor


@pytest.fixture(scope="function")
def log_config(database_connection):
    with open("log_config.yaml", "r") as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield log_config


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("ga4gh/wes/20191217_workflow_execution_service.swagger.yaml", "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
        yield swagger
