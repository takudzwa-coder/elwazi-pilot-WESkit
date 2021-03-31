import copy
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from test_utils import get_mock_run


def test_insert_and_load_run(test_database):
    run1 = get_mock_run(workflow_url="tests/wf1/Snakefile",
                        workflow_type="snakemake")
    assert test_database.insert_run(run1)
    run2 = test_database.get_run(run1.run_id)
    assert run1 == run2
    run_id_and_states = test_database.list_run_ids_and_states()
    assert len(run_id_and_states) == 1


def test_update_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake")
    assert test_database.insert_run(run)
    new_run = copy.copy(run)
    new_run.run_status = RunStatus.RUNNING
    test_database.update_run(new_run)
    assert new_run.run_status == RunStatus.RUNNING
    assert run.run_status == RunStatus.UNKNOWN


def test_get_runs(test_database):
    runs = test_database.get_runs(query={})
    assert len(runs) > 0
    for run in runs:
        assert isinstance(run, Run)


def test_count_states(test_database):
    counts = test_database.count_states()
    for status in RunStatus:
        assert status.name in counts.keys()


def test_delete_run(test_database):
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake")
    assert test_database.insert_run(run)
    assert test_database.delete_run(run)
    find_run = test_database.get_run(run.run_id)
    assert find_run is None
