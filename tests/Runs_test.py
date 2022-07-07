#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import uuid
from pathlib import Path

import pytest
from bson import CodecOptions, UuidRepresentation
from pymongo import MongoClient

from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.utils import updated, now

mock_run_data = {
    "id": uuid.uuid4(),
    "status": RunStatus.INITIALIZING,
    "request_time": None,
    "user_id": "test_id",
    "request": {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    },
    "celery_task_id": "the_task_id",
    "sub_dir": Path("some/dir"),
    "rundir_rel_workflow_path": Path("some/path"),
    "start_time": now(),
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
    new_run = Run(**mock_run_data)
    new_run.status = RunStatus.RUNNING
    client = MongoClient(database_container.get_connection_url())
    db = client["WES"]
    collection = db.get_collection("test_runs",
                                   codec_options=CodecOptions(
                                       uuid_representation=UuidRepresentation.STANDARD))
    collection.insert_one(new_run.to_bson_serializable())
    data = collection.find(projection={"_id": False})
    for x in data:
        load_run = Run.from_bson_serializable(x)
        if load_run.id == new_run.id:
            assert dict(load_run) == dict(new_run)


def test_run_modification():
    run = Run(**mock_run_data)
    assert not run.modified

    run.status = RunStatus.RUNNING
    assert run.modified


def test_run_merge_throws_incompatbile_runs():
    run1 = Run(**mock_run_data)
    run2 = Run(**updated(mock_run_data, id="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run2)

    run3 = Run(**updated(mock_run_data, user_id="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run3)

    run4 = Run(**updated(mock_run_data, request={}))
    with pytest.raises(RuntimeError):
        run1.merge(run4)

    run5 = Run(**updated(mock_run_data, request_time="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run5)


def test_run_merge_throws_ambiguous_changes():
    run_data = mock_run_data
    run1 = Run(**run_data)
    run2 = Run(**updated(run_data, celery_task_id="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run2)

    run3 = Run(**updated(run_data, sub_dir=Path("incompatible")))
    with pytest.raises(RuntimeError):
        run1.merge(run3)

    run4 = Run(**updated(run_data, rundir_rel_workflow_path=Path("incompatible")))
    with pytest.raises(RuntimeError):
        run1.merge(run4)

    run5 = Run(**updated(run_data, start_time=now()))
    with pytest.raises(RuntimeError):
        run1.merge(run5)

    run6 = Run(**updated(run_data, stdout="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run6)

    run7 = Run(**updated(run_data, stderr="incompatible"))
    with pytest.raises(RuntimeError):
        run1.merge(run7)

    run8 = Run(**updated(run_data, execution_log={"incompatible": "incompatible"}))
    with pytest.raises(RuntimeError):
        run1.merge(run8)

    run9 = Run(**updated(run_data, task_logs=["incompatible"]))
    with pytest.raises(RuntimeError):
        run1.merge(run9)


def test_run_merge_merges_none():
    run_data = mock_run_data
    run1 = Run(**run_data)

    run2 = Run(**updated(run_data, celery_task_id=None))
    assert run1.merge(run2).celery_task_id == run1.celery_task_id

    run3 = Run(**updated(run_data, sub_dir=None))
    assert run1.merge(run3).sub_dir == run1.sub_dir

    run4 = Run(**updated(run_data, rundir_rel_workflow_path=None))
    assert run1.merge(run4).rundir_rel_workflow_path == run1.rundir_rel_workflow_path

    run5 = Run(**updated(run_data, start_time=None))
    assert run1.merge(run5).start_time == run1.start_time

    run6 = Run(**updated(run_data, stdout=None))
    assert run1.merge(run6).stdout == run1.stdout

    run7 = Run(**updated(run_data, stderr=None))
    assert run1.merge(run7).stderr == run1.stderr


def test_run_merge_merges_outputs():
    run1 = Run(**mock_run_data)
    run2 = Run(**updated(mock_run_data,
                         outputs={
                            "group_b": ["file_b1", "file_b2"]
                         }))
    merged = run1.merge(run2)
    assert {key: set(values) for key, values in merged.outputs.items()} == {
        "group_a": {"file_a1"},
        "group_b": {"file_b1", "file_b2", "file_b100"}
    }


def test_run_merge_progresses_state():
    init = Run(**mock_run_data)
    queued = Run(**updated(mock_run_data, status=RunStatus.QUEUED))
    running = Run(**updated(mock_run_data, status=RunStatus.RUNNING))
    completed = Run(**updated(mock_run_data, status=RunStatus.COMPLETE))
    system_error = Run(**updated(mock_run_data, status=RunStatus.SYSTEM_ERROR))
    paused = Run(**updated(mock_run_data, status=RunStatus.PAUSED))

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
