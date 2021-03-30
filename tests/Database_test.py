import copy
import os
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from test_utils import get_mock_run


def test_insert_and_load_run(database):
    run1 = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                  "tests/wf1/Snakefile"),
                        workflow_type="snakemake")
    assert database.insert_run(run1)
    run2 = database.get_run(run1.run_id)
    assert run1 == run2
    run_id_and_states = database.list_run_ids_and_states()
    assert len(run_id_and_states) == 1


def test_update_run(database):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf1/Snakefile"),
                       workflow_type="snakemake")
    assert database.insert_run(run)
    new_run = copy.copy(run)
    new_run.run_status = RunStatus.RUNNING
    database.update_run(new_run)
    assert new_run.run_status == RunStatus.RUNNING
    assert run.run_status == RunStatus.UNKNOWN


def test_get_runs(database):
    runs = database.get_runs(query={})
    assert len(runs) > 0
    for run in runs:
        assert isinstance(run, Run)


def test_count_states(database):
    counts = database.count_states()
    for status in RunStatus:
        assert status.name in counts.keys()


def test_delete_run(database):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf1/Snakefile"),
                       workflow_type="snakemake")
    assert database.insert_run(run)
    assert database.delete_run(run)
    find_run = database.get_run(run.run_id)
    assert find_run is None
