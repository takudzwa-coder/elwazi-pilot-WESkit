# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import uuid
from pathlib import Path

import pytest
from bson import CodecOptions, UuidRepresentation
from pymongo import MongoClient

from weskit.classes.Run import Run
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.utils import updated, now

mock_run_data = {
    "id": uuid.uuid4(),
    "processing_stage": ProcessingStage.RUN_CREATED,
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
    new_run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION
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

    another_run = Run(**mock_run_data)
    another_run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION
    assert another_run.modified


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


def test_run_merge_processing_stage():
    init = Run(**mock_run_data)
    prepared_execution = Run(**updated(mock_run_data,
                             processing_stage=ProcessingStage.PREPARED_EXECUTION))
    submitted_execution = Run(**updated(mock_run_data,
                              processing_stage=ProcessingStage.SUBMITTED_EXECUTION))
    finished = Run(**updated(mock_run_data, processing_stage=ProcessingStage.FINISHED_EXECUTION))
    paused = Run(**updated(mock_run_data, processing_stage=ProcessingStage.PAUSED))
    system_error = Run(**updated(mock_run_data, processing_stage=ProcessingStage.SYSTEM_ERROR))
    executor_error = Run(**updated(mock_run_data, processing_stage=ProcessingStage.EXECUTOR_ERROR))

    canceled = Run(**updated(mock_run_data, processing_stage=ProcessingStage.CANCELED))

    assert init.merge(prepared_execution).processing_stage == ProcessingStage.PREPARED_EXECUTION
    assert init.merge(submitted_execution).processing_stage == ProcessingStage.SUBMITTED_EXECUTION
    assert init.merge(finished).processing_stage == ProcessingStage.FINISHED_EXECUTION
    assert init.merge(system_error).processing_stage == ProcessingStage.SYSTEM_ERROR
    assert init.merge(executor_error).processing_stage == ProcessingStage.EXECUTOR_ERROR

    assert finished.merge(finished).processing_stage == ProcessingStage.FINISHED_EXECUTION
    assert submitted_execution.merge(system_error).processing_stage == ProcessingStage.SYSTEM_ERROR
    assert submitted_execution.merge(executor_error).processing_stage == \
        ProcessingStage.EXECUTOR_ERROR
    assert submitted_execution.merge(paused).processing_stage == ProcessingStage.PAUSED

    assert prepared_execution.merge(finished).processing_stage == ProcessingStage.FINISHED_EXECUTION
    assert submitted_execution.merge(canceled).processing_stage == \
        ProcessingStage.CANCELED


# test higher precedence
    assert prepared_execution.merge(submitted_execution).processing_stage == \
        ProcessingStage.SUBMITTED_EXECUTION
    assert submitted_execution.merge(finished).processing_stage == \
        ProcessingStage.FINISHED_EXECUTION
