import sys, uuid, pytest
from pymongo import MongoClient
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus

mock_run_data = {
    "run_id": str(uuid.uuid4()),
    "run_status": "UNKNOWN",
    "request_time": None,
    "request": {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    },
}

def test_create_and_load_run(database_container):
    new_run = Run(mock_run_data)
    new_run.run_status = RunStatus.RUNNING
    client = MongoClient(database_container.get_connection_url())
    db = client["WES"]
    collection = db["test_runs"]
    collection.insert_one(new_run.get_data())
    data = collection.find()
    for x in data:
        load_run = Run(x)
        if load_run.run_id == new_run.run_id:
            assert load_run.get_data() == new_run.get_data()

def test_create_run_fails(database_container):
    with pytest.raises(Exception):
        Run({})
