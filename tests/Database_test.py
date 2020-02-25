import pytest
import time
from ga4gh.wes.Database import Database
from ga4gh.wes.RunStatus import RunStatus
from testcontainers.mongodb import MongoDbContainer
from pymongo import MongoClient

@pytest.fixture(scope="function")
def database_connection():
    container = MongoDbContainer('mongo:4.2.3')
    container.start()
    time.sleep(120)
    database = Database(MongoClient(container.get_connection_url()), "WES_Test")
    yield database
    database._db_runs().drop()


run_id = "test_store_and_retrieve_run_id"
    

def test_create_new_run(database_connection):
    print("test create_new_run")
    run = database_connection.create_new_run(run_id, [])
    assert RunStatus.decode(run["run_status"]) == RunStatus.NotStarted
    assert run["run_id"] == run_id


def test_get_run(database_connection):
    print("test get_run")
    database_connection.create_new_run(run_id, [])
    run = database_connection.get_run(run_id)
    assert run["run_id"] == run_id


def test_list_run_ids_and_states(database_connection):
    print("test list_run_ids_and_states")
    run_id_and_states = database_connection.list_run_ids_and_states()
    assert len(run_id_and_states) == 0
    database_connection.create_new_run(run_id, [])
    run_id_and_states = database_connection.list_run_ids_and_states()
    assert len(run_id_and_states) == 1
    assert run_id_and_states[0]["run_id"] == run_id
    assert RunStatus.decode(run_id_and_states[0]["run_status"]) == RunStatus.NotStarted


def test_update_run(database_connection):
    print("test update_run")
    run = database_connection.create_new_run(run_id, [])
    new_run = run.copy()
    new_run["run_status"] = RunStatus.Running.encode()
    database_connection.update_run(new_run)
    assert new_run["run_id"] == run_id
    assert RunStatus.decode(new_run["run_status"]) == RunStatus.Running
    assert RunStatus.decode(run["run_status"]) == RunStatus.NotStarted


def test_delete_run(database_connection):
    print("test delete_run")
    database_connection.create_new_run(run_id, [])
    database_connection.delete_run(run_id)
    find_run = database_connection.get_run(run_id)
    assert find_run is None
