from wesnake.classes.RunStatus import RunStatus

def test_create_and_load_run(database_connection):
    print("test create_new_run")
    run1 = database_connection.create_new_run([])
    assert RunStatus.decode(run1["run_status"]) == RunStatus.UNKNOWN
    run2 = database_connection.get_run(run1["run_id"])
    assert run1 == run2
    run_id_and_states = database_connection.list_run_ids_and_states()
    assert len(run_id_and_states) == 1

def test_update_run(database_connection):
    print("test update_run")
    run = database_connection.create_new_run([])
    new_run = run.copy()
    new_run["run_status"] = RunStatus.RUNNING.encode()
    database_connection.update_run(new_run)
    assert RunStatus.decode(new_run["run_status"]) == RunStatus.RUNNING
    assert RunStatus.decode(run["run_status"]) == RunStatus.UNKNOWN

def test_delete_run(database_connection):
    print("test delete_run")
    run = database_connection.create_new_run([])
    database_connection.delete_run(run["run_id"])
    find_run = database_connection.get_run(run["run_id"])
    assert find_run is None
