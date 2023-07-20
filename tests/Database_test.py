#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import copy

import pytest

from weskit.exceptions import DatabaseOperationError, ConcurrentModificationError
from test_utils import get_mock_run
from weskit.classes.Run import Run
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.utils import updated


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


@pytest.mark.integration
def test_except_on_duplicate_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    test_database.insert_run(run)
    with pytest.raises(DatabaseOperationError):
        test_database.insert_run(run)


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


@pytest.mark.integration
def test_except_update_on_missing_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    # Modify the run, to ensure an update is attempted.
    run.processing_stage = ProcessingStage.SUBMITTED_EXECUTION
    with pytest.raises(DatabaseOperationError):
        test_database.update_run(run)


@pytest.mark.integration
def test_get_runs(test_database):
    runs = test_database.get_runs(query={})
    assert len(runs) > 0
    for run in runs:
        assert isinstance(run, Run)


@pytest.mark.integration
def test_delete_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    test_database.insert_run(run)
    assert test_database.delete_run(run)
    find_run = test_database.get_run(run.id)
    assert find_run is None
