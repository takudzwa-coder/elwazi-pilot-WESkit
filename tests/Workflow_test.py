#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import os
import re
import time
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict

from test_utils import get_mock_run, is_within_timeout, assert_status_is_not_failed
from weskit.classes.RunStatus import RunStatus
from weskit.exceptions import ClientError
from weskit.utils import to_filename


@pytest.mark.integration
def test_snakemake_prepare_execution(manager, manager_rundir):

    # 1.) use workflow on server
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    assert run.status == RunStatus.INITIALIZING

    # 2.) workflow does neither exist on server nor in attachment
    #     -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Filesnake",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0")
    try:
        manager.database.insert_run(run)
        manager.prepare_execution(run, files=[])
    except ClientError as e:
        regex = re.compile("Derived workflow path is not accessible:")
        assert re.search(regex, e.message) is not None

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment": [wf_file]})
        run = get_mock_run(workflow_url=wf_url,
                           workflow_type="SMK",
                           workflow_type_version="6.10.0")
        manager.database.insert_run(run)
        run = manager.prepare_execution(run, files)
    assert run.status == RunStatus.INITIALIZING
    assert run.workflow_path(manager.weskit_context).is_file()

    # 4.) set custom workdir
    run = get_mock_run(workflow_url="tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0",
                       tags={"run_dir": "sample1/my_workdir"})
    run = manager_rundir.prepare_execution(run, files=[])
    assert run.status == RunStatus.INITIALIZING
    assert run.sub_dir == Path("sample1/my_workdir")


@pytest.mark.integration
def test_execute_snakemake(manager,
                           celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0",
                       workflow_engine_parameters={})
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        status = run.status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    assert run.run_dir(manager.weskit_context) / "hello_world.txt"
    assert "hello_world.txt" in to_filename(run.outputs["workflow"])

    assert run.execution_log["env"] == {}
    assert run.execution_log["cmd"] == [
        "snakemake",
        "--snakefile",
        str(run.rundir_rel_workflow_path),
        "--cores", "1",
        "--configfile",
        "config.yaml"
    ]


@pytest.mark.integration
def test_fail_execute_snakemake(manager,
                                celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0",
                       workflow_engine_parameters={},
                       workflow_params={"missing": "variable"})
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        status = run.status
        if status != RunStatus.EXECUTOR_ERROR:
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    assert run.execution_log["exit_code"] != 0
    assert not (manager.weskit_context.run_dir(run.sub_dir) / "hello_world.txt").exists()
    assert "hello_world.txt" not in to_filename(run.outputs["workflow"])

    assert run.execution_log["env"] == {}
    assert run.execution_log["cmd"] == [
        "snakemake",
        "--snakefile",
        str(run.rundir_rel_workflow_path),
        "--cores", "1",
        "--configfile",
        "config.yaml"
    ]


@pytest.mark.integration
def test_execute_nextflow(manager,
                          celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf3/helloworld.nf",
                       workflow_type="NFL",
                       workflow_type_version="21.04.0",
                       workflow_engine_parameters={"trace": "False"})
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        status = run.status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    assert run.run_dir(manager.weskit_context) / "hello_world.txt"
    hello_world_files = list(filter(lambda name: os.path.basename(name) == "hello_world.txt",
                                    run.outputs["workflow"]))
    assert len(hello_world_files) == 2, hello_world_files   # 1 actual file + 1 publish symlink
    with open(run.run_dir(manager.weskit_context) / hello_world_files[0], "r") as fh:
        assert fh.readlines() == ["hello_world\n"]

    assert run.execution_log["env"] == {"NXF_OPTS": "-Xmx256m"}
    assert run.execution_log["cmd"] == [
        "nextflow",
        "-Djava.io.tmpdir=/tmp",
        "run",
        str(run.rundir_rel_workflow_path),
        "-params-file", "config.yaml",
        "-with-timeline",
        "-with-dag",
        "-with-report"
    ]


# Celery's revoke function applied to the Snakemake job results in a change
# of the main process's working directory, if a celery_session_worker is
# used. Therefore, the test should use a celery_worker. THIS does NOT solve
# the general problem though, if in production workers are reused for new
# tasks!
@pytest.mark.skip
def test_cancel_workflow(manager, celery_worker):
    run = get_mock_run(workflow_url="tests/wf2/Snakefile",
                       workflow_type="SMK")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    # Before we cancel, we need to wait that the execution actually started.
    # Cancellation of the preparation is not implemented.
    time.sleep(5)
    manager.cancel(run)
    assert run.run_status == RunStatus.CANCELED


@pytest.mark.integration
def test_update_all_runs(manager,
                         celery_worker):
    run = get_mock_run(workflow_url="file:tests/wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="6.10.0")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    run = manager.database.update_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        status = run.status
        print("Waiting ... (status=%s)" % status.name)
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True

    manager.update_runs()
    db_run = manager.get_run(run.id)
    assert db_run is not None
    assert db_run.status == RunStatus.COMPLETE
