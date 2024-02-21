# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import copy

import pytest
import uuid

from weskit.exceptions import DatabaseOperationError, ConcurrentModificationError
from test_utils import get_mock_run
from weskit.classes.Run import Run
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.utils import updated
from weskit.classes.AbstractDatabase import MockDatabase


@pytest.mark.slow
@pytest.mark.integration
def test_insert_and_load_run(test_database):
    run1 = get_mock_run(workflow_url="tests/wf1/Snakefile",
                        workflow_type="SMK",
                        workflow_type_version="7.30.2",
                        user_id="test_id")
    test_database.insert_run(run1)
    run2 = test_database.get_run(run1.id)
    assert run1 == run2
    run_id_and_states = test_database.list_run_ids_and_stages("test_id")
    assert len(run_id_and_states) == 1


@pytest.mark.slow
@pytest.mark.integration
def test_except_on_duplicate_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    test_database.insert_run(run)
    with pytest.raises(DatabaseOperationError):
        test_database.insert_run(run)


@pytest.mark.slow
@pytest.mark.integration
def test_update_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    test_database.insert_run(run)
    new_run = copy.copy(run)
    # Runs in processing stage SUBMITTED_EXECUTION must have a celery_task_id.
    # Not nice: Interaction with test_update_all_runs via to DB.
    new_run.celery_task_id = "1245"
    new_run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION
    test_database.update_run(new_run)
    assert new_run.processing_stage == ProcessingStage.SUBMITTED_EXECUTION
    assert run.processing_stage == ProcessingStage.RUN_CREATED


@pytest.mark.slow
@pytest.mark.integration
def test_except_update_on_current_update(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")

    # Now simulate a concurrent run, by just changing the value before writing it to the database.
    # The only thing necessary is to modify the db_version counter. We don't do any content
    # comparisons.
    modified_run = Run(**updated(dict(run), db_version=run.db_version + 1))
    test_database.insert_run(modified_run)

    # Modify the run, to unsure an update is attempted.
    run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION

    # The old run and the modified run should be divergent now.
    with pytest.raises(ConcurrentModificationError):
        test_database.update_run(run)


@pytest.mark.slow
@pytest.mark.integration
def test_except_update_on_missing_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    # Modify the run, to ensure an update is attempted.
    run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION
    with pytest.raises(DatabaseOperationError):
        test_database.update_run(run)


@pytest.mark.slow
@pytest.mark.integration
def test_get_runs(test_database):
    runs = test_database.get_runs(query={})
    assert len(runs) > 0
    for run in runs:
        assert isinstance(run, Run)


@pytest.mark.slow
@pytest.mark.integration
def test_delete_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    test_database.insert_run(run)
    assert test_database.delete_run(run)
    find_run = test_database.get_run(run.id)
    assert find_run is None


mock_run_data = {
    "id": uuid.uuid4(),
    "processing_stage": ProcessingStage.RUN_CREATED,
    "request_time": None,
    "user_id": "test_id",
    "request": {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    },
    "exit_code": None,
    "sub_dir": None
}


@pytest.fixture
def mock_db():
    db = MockDatabase()
    return db


def test_create_run_id(mock_db):
    run_id = mock_db.create_run_id()
    assert isinstance(run_id, uuid.UUID)


def test_insert_run_and_get_run(mock_db):
    run = Run(**mock_run_data)
    mock_db.insert_run(run)

    retrieved_run = mock_db.get_run(run.id)

    assert retrieved_run == run.to_bson_serializable()
    assert retrieved_run is not None
    assert retrieved_run["id"] == run.id
    assert retrieved_run["processing_stage"] == "RUN_CREATED"
    assert retrieved_run["user_id"] == "test_id"
    assert retrieved_run["request"] == {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    }


def test_update_run_v2(mock_db):
    run = Run(**mock_run_data)
    mock_db.insert_run(run)

    run.processing_stage = ProcessingStage.FINISHED_EXECUTION
    updated_run = mock_db.update_run(run)

    assert updated_run.processing_stage == ProcessingStage.FINISHED_EXECUTION


def test_delete_run_v2(mock_db):
    run = Run(**mock_run_data)
    mock_db.insert_run(run)

    assert mock_db.delete_run(run)
    assert mock_db.get_run(run.id) is None


def test_list_run_ids_and_stages_and_times(mock_db):
    run1 = Run(**mock_run_data)
    run2 = Run(**{
                    "id": uuid.uuid4(),
                    "processing_stage": ProcessingStage.RUN_CREATED,
                    "request_time": None,
                    "user_id": "test_id",
                    "request": {
                        "workflow_url": "",
                        "workflow_params": '{"text":"hello_world"}'
                    }
                 }
               )
    run2.processing_stage = ProcessingStage.FINISHED_EXECUTION
    mock_db.insert_run(run1)
    mock_db.insert_run(run2)

    user_id = run1.user_id  # user_id is the same for both runs
    run_list = mock_db.list_run_ids_and_stages_and_times(user_id)
    assert len(run_list) == 2
    assert run_list[0]["user_id"] == run1.user_id
    assert run_list[0]["run_stage"] == "RUN_CREATED"
    assert run_list[1]["user_id"] == run2.user_id
    assert run_list[1]["run_stage"] == "FINISHED_EXECUTION"
