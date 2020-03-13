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
    executor = ServiceInfo(service_info, database_connection)
    yield executor
