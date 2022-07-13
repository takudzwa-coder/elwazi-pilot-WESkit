#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import json
import time
import uuid
from typing import Dict, Optional

import yaml

from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.utils import now


def get_mock_run(workflow_url,
                 workflow_type,
                 workflow_type_version,
                 workflow_engine_parameters=None,
                 tags=None,
                 user_id="test_id",
                 workflow_params=None):
    workflow_engine_parameters = {}\
        if workflow_engine_parameters is None\
        else workflow_engine_parameters
    data = {
        "id": uuid.uuid4(),
        "status": RunStatus.INITIALIZING,
        "request_time": None,
        "user_id": user_id,
        "request": {
            "workflow_url": workflow_url,
            "workflow_type": workflow_type,
            "workflow_type_version": workflow_type_version,
            "workflow_params": {"text": "hello_world"}
            if workflow_params is None else workflow_params,
            "workflow_engine_parameters": workflow_engine_parameters
        },
        "execution_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    }
    if tags is not None:
        data["request"]["tags"] = tags
    run = Run(**data)
    return run


def is_within_timeout(start_time, timeout=30) -> bool:
    return (time.time() - start_time) <= timeout


def assert_within_timeout(start_time, timeout=30):
    assert is_within_timeout(start_time, timeout), "Test timed out"


def is_run_failed(status: RunStatus) -> bool:
    return status in [
        RunStatus.EXECUTOR_ERROR,
        RunStatus.SYSTEM_ERROR,
        RunStatus.CANCELED,
        RunStatus.CANCELING
    ]


def get_workflow_data(snakefile, config, engine_params: Optional[Dict[str, str]] = None):
    engine_params = {} if engine_params is None else engine_params
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "SMK",
        "workflow_type_version": "6.10.0",
        "workflow_url": snakefile,
        "workflow_engine_parameters": json.dumps(engine_params)
    }
    return data


def assert_status_is_not_failed(status: RunStatus):
    assert not is_run_failed(status), "Failing run status '{}'".format(status.name)


def test_now_has_no_nanoseconds():
    t = now().timestamp()   # time in POSIX format: float in microseconds
    assert t - int(t) < 1
