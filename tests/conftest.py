import pytest
import os
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from pymongo import MongoClient


@pytest.fixture()
def database_connection(scope="function"):
    connection_url = os.environ["WESNAKE_TEST"]
    database = Database(MongoClient(connection_url), "WES_Test")
    yield database
    database._db_runs().drop()

@pytest.fixture(scope="function")
def snakemake_executor():
    executor = Snakemake()
    yield executor