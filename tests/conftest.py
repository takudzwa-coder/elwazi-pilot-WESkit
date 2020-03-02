import pytest
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer

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