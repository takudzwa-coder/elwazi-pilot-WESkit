import copy
from wesnake.classes.RunStatus import RunStatus

def test_create_and_load_run(database_connection):
    print("test create_new_run")
    run1 = database_connection.create_new_run({})
    assert run1.check_status("UNKNOWN")
    run2 = database_connection.get_run(run1.run_id)
    assert run1.get_data() == run2.get_data()
    run_id_and_states = database_connection.list_run_ids_and_states()
    assert len(run_id_and_states) == 1

def test_update_run(database_connection):
    print("test update_run")
    run = database_connection.create_new_run({})
    new_run = copy.copy(run)
    new_run.run_status = ("RUNNING")
    database_connection.update_run(new_run)
    assert new_run.check_status("RUNNING")
    assert run.check_status("UNKNOWN")

def test_delete_run(database_connection):
    print("test delete_run")
    run = database_connection.create_new_run([])
    database_connection.delete_run(run)
    find_run = database_connection.get_run(run.run_id)
    assert find_run is None
