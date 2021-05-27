#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import uuid

from weskit.classes.RunStatus import RunStatus
from weskit.classes.Run import Run
import time


def get_mock_run(workflow_url, workflow_type, tags=None, user_id="test_id"):
    data = {
        "run_id": str(uuid.uuid4()),
        "run_status": "INITIALIZING",
        "request_time": None,
        "user_id": user_id,
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


def is_within_timout(start_time, timeout=30) -> bool:
    return (time.time() - start_time) <= timeout


def assert_within_timeout(start_time, timeout=30):
    assert is_within_timout(start_time, timeout), "Test timed out"


def is_run_failed(status: RunStatus) -> bool:
    return status in [
        RunStatus.UNKNOWN,
        RunStatus.EXECUTOR_ERROR,
        RunStatus.SYSTEM_ERROR,
        RunStatus.CANCELED,
        RunStatus.CANCELING
    ]


def assert_status_is_not_failed(status: RunStatus):
    assert not is_run_failed(status), "Failing run status '{}'".format(status.name)
