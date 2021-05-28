#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import uuid
from weskit.classes.Run import Run
import time
import yaml


def get_mock_run(workflow_url, workflow_type, tags=None):
    data = {
        "run_id": str(uuid.uuid4()),
        "run_status": "INITIALIZING",
        "request_time": None,
        "user_id": "test_id",
        "request": {
            "workflow_url": workflow_url,
            "workflow_type": workflow_type,
            "workflow_params": {"text": "hello_world"},
        },
        "execution_path": [],
        "run_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    }
    if tags is not None:
        data["request"]["tags"] = tags
    run = Run(data)
    return run


def get_run_success(status, start_time):
    assert (time.time() - start_time) <= 30, "Test timed out"

    print("Waiting ... (status=%s)" % status)
    if status in ["UNKNOWN", "EXECUTOR_ERROR", "SYSTEM_ERROR", "CANCELED", "CANCELING"]:
        assert False, "Failing run status '{}'".format(status)

    if status == "COMPLETE":
        return True

    return False


def get_workflow_data(snakefile, config):
    with open(config) as file:
        workflow_params = yaml.load(file, Loader=yaml.FullLoader)

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": "file:tests/wf1/Snakefile"
    }
    return data
