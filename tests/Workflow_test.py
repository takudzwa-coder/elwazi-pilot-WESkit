import time
import os
from weskit.utils import to_filename
from weskit.classes.Database import Database
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict
from test_utils import get_mock_run
from weskit.classes.RunStatus import RunStatus


def test_snakemake_prepare_execution(manager):

    # 1.) use workflow on server
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"),
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.INITIALIZING

    # 2.) workflow does not exist on server -> error message outputs execution
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Filesnake"),
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.SYSTEM_ERROR
    assert os.path.isfile(run.outputs["execution"])

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment":[wf_file]})
        run = get_mock_run(workflow_url=wf_url,
                           workflow_type="snakemake")
        run = manager.prepare_execution(run, files)
    assert run.run_status == RunStatus.INITIALIZING
    assert os.path.isfile(os.path.join(run.execution_path, wf_url))

    # 4.) workflow is not attached -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.SYSTEM_ERROR
    assert os.path.isfile(run.outputs["execution"])


def test_execute_snakemake(database: Database, manager, celery_worker):
    test_failed_status = [
       RunStatus.UNKNOWN,
       RunStatus.EXECUTOR_ERROR,
       RunStatus.SYSTEM_ERROR,
       RunStatus.CANCELED,
       RunStatus.CANCELING
       ]
    timeout_seconds = 120
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf1/Snakefile"),
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert (start_time - time.time()) <= timeout_seconds, "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert not status in test_failed_status
            print("Waiting ...")
            time.sleep(1)
            run = manager.update_run(run)
            database.update_run(run)
            continue
        assert os.path.isfile(
            os.path.join(run.execution_path, "hello_world.txt"))
        assert "hello_world.txt" in run.outputs["Workflow"]
        success = True


def test_execute_nextflow(database: Database, manager, celery_worker):
    test_failed_status = [
       RunStatus.UNKNOWN,
       RunStatus.EXECUTOR_ERROR,
       RunStatus.SYSTEM_ERROR,
       RunStatus.CANCELED,
       RunStatus.CANCELING
       ]
    timeout_seconds = 120
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf3/helloworld.nf"),
                       workflow_type="nextflow")
    run = manager.prepare_execution(run, files=[])
    manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert (start_time - time.time()) <= timeout_seconds, "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert not status in test_failed_status
            print("Waiting ...")
            time.sleep(1)
            run = manager.update_run(run)
            database.update_run(run)
            continue
        assert os.path.isfile(
            os.path.join(run.execution_path, "hello_world.txt"))
        assert "hello_world.txt" in to_filename(run.outputs["Workflow"])
        success = True



def test_cancel_workflow(manager, celery_worker, redis_container):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf2/Snakefile"),
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.cancel(run)
    assert run.run_status == RunStatus.CANCELED


def test_update_all_runs(manager, celery_worker, database):
    test_failed_status = [
        RunStatus.UNKNOWN,
        RunStatus.EXECUTOR_ERROR,
        RunStatus.SYSTEM_ERROR,
        RunStatus.CANCELED,
        RunStatus.CANCELING
    ]
    timeout_seconds = 120
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(),
                                                 "tests/wf1/Snakefile"),
                       workflow_type="snakemake")
    database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    database.update_run(run)
    start_time = time.time()
    success = False
    while not success:
        assert (start_time - time.time()) <= timeout_seconds, "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert not status in test_failed_status
            print("Waiting ...")
            time.sleep(1)
            run = manager.update_state(run)
            continue
        manager.update_runs(database, query={})
        db_run = database.get_run(run_id=run.run_id)
        assert db_run.run_status == RunStatus.COMPLETE
        success = True

