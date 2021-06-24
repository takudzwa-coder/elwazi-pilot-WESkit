#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import uuid
import pytest
from pymongo import MongoClient
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus

mock_run_data = {
    "run_id": str(uuid.uuid4()),
    "run_status": "INITIALIZING",
    "request_time": None,
    "user_id": "test_id",
    "request": {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    },
}


@pytest.mark.integration
def test_create_and_load_run(database_container):
    new_run = Run(mock_run_data)
    new_run.status = RunStatus.RUNNING
    client = MongoClient(database_container.get_connection_url())
    db = client["WES"]
    collection = db["test_runs"]
    collection.insert_one(dict(new_run))
    data = collection.find()
    for x in data:
        load_run = Run(x)
        if load_run.id == new_run.id:
            assert dict(load_run) == dict(new_run)


def test_create_run_fails():
    with pytest.raises(Exception):
        Run({})
