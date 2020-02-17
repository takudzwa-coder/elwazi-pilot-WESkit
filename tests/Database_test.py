import pytest
from ga4gh.wes.Database import Database
from ga4gh.wes.RunStatus import RunStatus
from pymongo import MongoClient


@pytest.fixture(scope="module")
def database_connection():
    database = Database(MongoClient(), "WES_Test")
    yield database
    database.drop()


def test_create_run(database_connection):
    run_id = "test_store_and_retrieve_run_id"
    run = database_connection.create_new_run(run_id, [])
    assert run.run_status == RunStatus.NotStarted