#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import time
import os

import pytest

from weskit.ClientError import ClientError
from weskit.utils import to_filename
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict
from utils import get_mock_run, is_within_timout, assert_status_is_not_failed
from weskit.classes.RunStatus import RunStatus


@pytest.mark.integration
def test_snakemake_prepare_execution(manager):

    # 1.) use workflow on server
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake",
                       workflow_type_version="5.8.2")
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.INITIALIZING

    # 2.) workflow does neither exist on server nor in attachment
    #     -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Filesnake",
                       workflow_type="snakemake",
                       workflow_type_version="5.8.2")
    with pytest.raises(ClientError):
        run = manager.prepare_execution(run, files=[])

    assert run.run_status == RunStatus.SYSTEM_ERROR
    assert os.path.isfile(run.outputs["execution"])

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment": [wf_file]})
        run = get_mock_run(workflow_url=wf_url,
                           workflow_type="snakemake",
                           workflow_type_version="5.8.2")
        run = manager.prepare_execution(run, files)
    assert run.run_status == RunStatus.INITIALIZING
    assert os.path.isfile(os.path.join(run.execution_path, wf_url))

    # 4.) set custom workdir
    manager.require_workdir_tag = True
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="snakemake",
                       workflow_type_version="5.8.2",
                       tags={"run_dir": "sample1/my_workdir"})
    run = manager.prepare_execution(run, files=[])
    assert run.run_status == RunStatus.INITIALIZING
    assert run.execution_path.endswith("sample1/my_workdir")
    manager.require_workdir_tag = False


@pytest.mark.integration
def test_execute_snakemake(manager,
                           celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="snakemake",
                       workflow_type_version="5.8.2")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert is_within_timout(start_time), "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True

    assert os.path.isfile(
        os.path.join(run.execution_path, "hello_world.txt"))
    assert "hello_world.txt" in to_filename(run.outputs["workflow"])

    assert run.execution_log["env"] == {"SOME_VAR": "with value"}
    assert run.execution_log["cmd"] == [
        "snakemake",
        "--snakefile",
        run.workflow_path,
        "--cores",
        "1",
        "--configfile",
        "%s/config.yaml" % run.execution_path
    ]


@pytest.mark.integration
def test_execute_nextflow(manager,
                          celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf3/helloworld.nf",
                       workflow_type="nextflow",
                       workflow_type_version="20.10.0")
    run = manager.prepare_execution(run, files=[])
    manager.execute(run)
    start_time = time.time()
    success = False
    while not success:
        assert is_within_timout(start_time), "Test timed out"
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
            continue
        assert os.path.isfile(
            os.path.join(run.execution_path, "hello_world.txt"))
        hello_world_files = list(filter(lambda name: os.path.basename(name) == "hello_world.txt",
                                        run.outputs["workflow"]))
        assert len(hello_world_files) == 2, hello_world_files   # 1 actual file + 1 publish symlink
        with open(os.path.join(run.execution_path, hello_world_files[0]), "r") as fh:
            assert fh.readlines() == ["hello_world\n"]
        success = True

    assert run.execution_log["env"] == {"NXF_OPTS": "-Xmx256m"}
    assert run.execution_log["cmd"] == [
        "nextflow",
        "-Djava.io.tmpdir=/tmp",
        "run",
        run.workflow_path,
        "-params-file",
        "%s/config.yaml" % run.execution_path,
        "-with-trace",
        "-with-timeline",
        "-with-dag",
        "-with-report"
    ]


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
def test_update_all_runs(manager,
                         celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="snakemake",
                       workflow_type_version="5.8.2")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.update_run(run)
    start_time = time.time()
    success = False
    while not success:
        assert is_within_timout(start_time), "Test timed out"
        status = run.run_status
        print("Waiting ... (status=%s)" % status.name)
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            time.sleep(1)
            run = manager.update_state(run)
            continue
        manager.update_runs(query={})
        db_run = manager.database.get_run(run_id=run.run_id)
        assert db_run.run_status == RunStatus.COMPLETE
        success = True
