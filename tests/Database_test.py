import copy, uuid, os
from wesnake.classes.Run import Run
from wesnake.classes.RunStatus import RunStatus

def get_mock_run(workflow_url):
    run = Run({
        "run_id": str(uuid.uuid4()),
        "run_status": "UNKNOWN",
        "request_time": None,
        "request": {
            "workflow_url": workflow_url,
            "workflow_params": '{"text":"hello_world"}'
        },
        "execution_path" : [],
        "run_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    })
    return run

def test_insert_and_load_run(database_connection):
    print("test create_new_run")
    run1 = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    assert database_connection.insert_run(run1)
    run2 = database_connection.get_run(run1.run_id)
    assert run1.get_data() == run2.get_data()
    run_id_and_states = database_connection.list_run_ids_and_states()
    assert len(run_id_and_states) == 1

def test_update_run(database_connection):
    print("test update_run")
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    assert database_connection.insert_run(run)
    new_run = copy.copy(run)
    new_run.run_status = ("RUNNING")
    database_connection.update_run(new_run)
    assert new_run.run_status_check("RUNNING")
    assert run.run_status_check("UNKNOWN")

def test_get_runs(database_connection):
    print("test update_run")
    runs = database_connection.get_runs(query={})
    assert len(runs) > 0
    for run in runs:
        assert isinstance(run, Run)

def test_delete_run(database_connection):
    print("test delete_run")
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    assert database_connection.insert_run(run)
    assert database_connection.delete_run(run)
    find_run = database_connection.get_run(run.run_id)
    assert find_run is None
