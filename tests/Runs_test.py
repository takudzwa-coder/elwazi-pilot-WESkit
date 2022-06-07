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
    "celery_task_id": "the_task_id",
    "run_dir": "some/dir",
    "workflow_path": "some/path",
    "start_time": "timestamp",
    "stdout": "uri",
    "stderr": "uri",
    "execution_log": {"some": "thing"},
    "task_logs": ["something"],
    "outputs": {
        "group_a": ["file_a1"],
        "group_b": ["file_b1", "file_b100"]
    }
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


def test_run_modification():
    run = Run(mock_run_data)
    assert not run.modified

    run.status = RunStatus.RUNNING
    assert run.modified


def test_run_merge_throws_incompatbile_runs():
    run1 = Run(mock_run_data)
    run2 = Run({**mock_run_data, "run_id": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run2)

    run3 = Run({**mock_run_data, "user_id": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run3)

    run4 = Run({**mock_run_data, "request": {}})
    with pytest.raises(RuntimeError):
        run1.merge(run4)

    run5 = Run({**mock_run_data, "request_time": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run5)


def test_run_merge_throws_ambiguous_changes():
    run_data = mock_run_data
    run1 = Run(run_data)
    run2 = Run({**run_data, "celery_task_id": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run2)

    run3 = Run({**run_data, "run_dir": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run3)

    run4 = Run({**run_data, "workflow_path": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run4)

    run5 = Run({**run_data, "start_time": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run5)

    run6 = Run({**run_data, "stdout": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run6)

    run7 = Run({**run_data, "stderr": "incompatible"})
    with pytest.raises(RuntimeError):
        run1.merge(run7)

    run8 = Run({**run_data, "execution_log": {"incompatible": "incompatible"}})
    with pytest.raises(RuntimeError):
        run1.merge(run8)

    run9 = Run({**run_data, "task_logs": ["incompatible"]})
    with pytest.raises(RuntimeError):
        run1.merge(run9)


def test_run_merge_merges_none():
    run_data = mock_run_data
    run1 = Run(run_data)

    run2 = Run({**run_data, "celery_task_id": None})
    assert run1.merge(run2).celery_task_id == run1.celery_task_id

    run3 = Run({**run_data, "run_dir": None})
    assert run1.merge(run3).dir == run1.dir

    run4 = Run({**run_data, "workflow_path": None})
    assert run1.merge(run4).workflow_path == run1.workflow_path

    run5 = Run({**run_data, "start_time": None})
    assert run1.merge(run5).start_time == run1.start_time

    run6 = Run({**run_data, "stdout": None})
    assert run1.merge(run6).stdout == run1.stdout

    run7 = Run({**run_data, "stderr": None})
    assert run1.merge(run7).stderr == run1.stderr


def test_run_merge_merges_outputs():
    run1 = Run(mock_run_data)
    run2 = Run({**mock_run_data,
                "outputs": {
                    "group_b": ["file_b1", "file_b2"]
                }})
    merged = run1.merge(run2)
    assert {key: set(values) for key, values in merged.outputs.items()} == {
        "group_a": {"file_a1"},
        "group_b": {"file_b1", "file_b2", "file_b100"}
    }


def test_run_merge_progresses_state():
    init = Run(mock_run_data)
    queued = Run({**mock_run_data, "run_status": RunStatus.QUEUED.name})
    running = Run({**mock_run_data, "run_status": RunStatus.RUNNING.name})
    completed = Run({**mock_run_data, "run_status": RunStatus.COMPLETE.name})
    system_error = Run({**mock_run_data, "run_status": RunStatus.SYSTEM_ERROR.name})
    paused = Run({**mock_run_data, "run_status": RunStatus.PAUSED.name})

    assert init.merge(queued).status == RunStatus.QUEUED
    assert init.merge(running).status == RunStatus.RUNNING
    assert init.merge(completed).status == RunStatus.COMPLETE
    assert init.merge(system_error).status == RunStatus.SYSTEM_ERROR
    assert init.merge(paused).status == RunStatus.PAUSED

    assert queued.merge(init).status == RunStatus.QUEUED, "Symmetric merge"
    assert system_error.merge(completed).status == RunStatus.SYSTEM_ERROR, "Symmetric merge"

    assert running.merge(paused).status == RunStatus.PAUSED, "Higher precedence used"
    assert running.merge(queued).status == RunStatus.RUNNING, "Higher precedence used"
    assert queued.merge(paused).status == RunStatus.PAUSED, "Higher precedence used"
