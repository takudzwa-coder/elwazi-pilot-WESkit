import sys, uuid
from pymongo import MongoClient
from wesnake.classes.Run import Run

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
    print(database_container.get_connection_url(), file=sys.stderr)
    new_run = Run(mock_run_data)
    new_run.set_status("RUNNING")
    print(new_run, file=sys.stderr)
    client = MongoClient(database_container.get_connection_url())
    db = client["WES"]
    collection = db["test_runs"]
    collection.insert_one(new_run.get_data())
    for x in collection.find():
        load_run = Run(x)
        print(load_run, file=sys.stderr)
        print(type(load_run), file=sys.stderr)
        print(load_run.get_status(), file=sys.stderr)