import time
import os

import pytest
from flask import current_app

from weskit.utils import to_filename
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict
from test_utils import get_mock_run
from weskit.classes.RunStatus import RunStatus


test_failed_status = [
       RunStatus.UNKNOWN,
       RunStatus.EXECUTOR_ERROR,
       RunStatus.SYSTEM_ERROR,
       RunStatus.CANCELED,
       RunStatus.CANCELING
    ]


@pytest.mark.integration
def test_snakemake_prepare_execution(manager):

    # 1.) use workflow on server
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.INITIALIZING

    # 2.) workflow does neither exist on server nor in attachment
    #     -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Filesnake",
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.SYSTEM_ERROR
    assert os.path.isfile(run.outputs["execution"])

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment": [wf_file]})
        run = get_mock_run(workflow_url=wf_url,
                           workflow_type="snakemake")
        run = manager.prepare_execution(run, files)
    assert run.run_status == RunStatus.INITIALIZING
    assert os.path.isfile(os.path.join(run.execution_path, wf_url))

    # 4.) set custom workdir
    manager.require_workdir_tag = True
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake",
                       tags={"run_dir":"sample1/my_workdir"})
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.INITIALIZING
    assert run.execution_path.endswith("sample1/my_workdir")
    manager.require_workdir_tag = False

@pytest.mark.integration
def test_execute_snakemake(test_client,
                           celery_worker):
    manager = current_app.manager
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="snakemake")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert (time.time() - start_time) <= 30, "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert status not in test_failed_status
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
            manager.database.update_run(run)
            continue
        assert os.path.isfile(
            os.path.join(run.execution_path, "hello_world.txt"))
        assert "hello_world.txt" in run.outputs["Workflow"]
        success = True


@pytest.mark.integration
def test_execute_nextflow(test_client,
                          celery_worker):
    manager = current_app.manager
    run = get_mock_run(workflow_url="file:tests/wf3/helloworld.nf",
                       workflow_type="nextflow")
    run = manager.prepare_execution(run, files=[])
    manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert (time.time() - start_time) <= 30, "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert status not in test_failed_status
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
            manager.database.update_run(run)
            continue
        assert os.path.isfile(
            os.path.join(run.execution_path, "hello_world.txt"))
        assert "hello_world.txt" in to_filename(run.outputs["Workflow"])
        success = True


# # Celery's revoke function applied to the Snakemake job results in a change
# # of the main process's working directory, if a celery_session_worker is
# # used. Therefore the test should use a celery_worker. THIS does NOT solve
# # the general problem though, if in production workers are reused for new
# # tasks!
# @pytest.mark.integration
# def test_cancel_workflow(manager, celery_worker):
#     run = get_mock_run(workflow_url="tests/wf2/Snakefile",
#                        workflow_type="snakemake")
#     run = manager.prepare_execution(run, files=[])
#     run = manager.execute(run)
#     # Before we cancel, we need to wait that the execution actually started.
#     # Cancellation of the preparation is not implemented.
#     time.sleep(5)
#     manager.cancel(run)
#     assert run.run_status == RunStatus.CANCELED


@pytest.mark.integration
def test_update_all_runs(test_client,
                         celery_worker):
    manager = current_app.manager
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="snakemake")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.update_run(run)
    start_time = time.time()
    success = False
    while not success:
        assert (time.time() - start_time) <= 30, "Test timed out"
        status = run.run_status
        print("Waiting ... (status=%s)" % status.name)
        if status != RunStatus.COMPLETE:
            assert status not in test_failed_status
            time.sleep(1)
            run = manager.update_state(run)
            continue
        manager.update_runs(query={})
        db_run = manager.database.get_run(run_id=run.run_id)
        assert db_run.run_status == RunStatus.COMPLETE
        success = True
