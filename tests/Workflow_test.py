# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import os
import re
import time
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict

from test_utils import get_mock_run, is_within_timeout, assert_stage_is_not_failed
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.exceptions import ClientError
from weskit.utils import to_filename


@pytest.mark.integration
def test_snakemake_prepare_execution(manager, manager_rundir):

    # 1.) use workflow on server
    run = get_mock_run(workflow_url="wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    assert run.processing_stage == ProcessingStage.PREPARED_EXECUTION

    # 2.) workflow does neither exist on server nor in attachment
    #     -> error message outputs execution
    run = get_mock_run(workflow_url="wf1/Filesnake",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    try:
        manager.database.insert_run(run)
        manager.prepare_execution(run, files=[])
    except ClientError as e:
        regex = re.compile("Derived workflow path is not accessible:")
        assert re.search(regex, e.message) is not None

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(manager.weskit_context.workflows_dir / "wf1/Snakefile", "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment": [wf_file]})
        run = get_mock_run(workflow_url=wf_url,
                           workflow_type="SMK",
                           workflow_type_version="7.30.2")
        manager.database.insert_run(run)
        run = manager.prepare_execution(run, files)
    assert run.processing_stage == ProcessingStage.PREPARED_EXECUTION
    assert run.workflow_path(manager.weskit_context).is_file()

    # 4.) set custom workdir
    run = get_mock_run(workflow_url="wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2",
                       tags={"run_dir": "sample1/my_workdir"})
    run = manager_rundir.prepare_execution(run, files=[])
    assert run.processing_stage == ProcessingStage.PREPARED_EXECUTION
    assert run.sub_dir == Path("sample1/my_workdir")

    # 5.) check relative "file:" scheme on custom workdir
    run = get_mock_run(workflow_url="wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2",
                       tags={"run_dir": "file:sample2/my_workdir"})
    run = manager_rundir.prepare_execution(run, files=[])
    assert run.processing_stage == ProcessingStage.PREPARED_EXECUTION
    assert run.sub_dir == Path("sample2/my_workdir")


@pytest.mark.integration
def test_execute_snakemake(manager,
                           celery_worker):
    # No path-processing is done on the engine environment path. Therefore, it has to be an
    # absolute path, or a path relative to the run directory -- both in the execution environment.
    engine_env_path = manager.executor_context.workflows_dir.absolute() / "wf1" / "env.sh"
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2",
                       workflow_engine_parameters={
                           "engine-environment": str(engine_env_path)
                       })
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        stage = run.processing_stage
        if stage != ProcessingStage.FINISHED_EXECUTION:
            assert_stage_is_not_failed(stage)
            print("Waiting ... (stage=%s)" % stage.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    assert run.run_dir(manager.weskit_context) / "hello_world.txt"
    assert "hello_world.txt" in to_filename(run.outputs["filesystem"])

    assert run.execution_log["env"] == {
        "CONDA_ENVS_PATH": "conda_envs/",
        "WESKIT_WORKFLOW_ENGINE": "SMK=7.30.2",
        "WESKIT_WORKFLOW_PATH": str(run.rundir_rel_workflow_path)
    }
    assert run.execution_log["cmd"] == [
        "set", "-eu", "-o", "pipefail", "&&",
        "source", str(engine_env_path), "&&",
        "snakemake",
        "--snakefile",
        str(run.rundir_rel_workflow_path),
        "--cores", "1",
        "--configfile",
        f"{run.id}.yaml"
    ]


@pytest.mark.integration
def test_fail_execute_snakemake(manager,
                                celery_worker):
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2",
                       workflow_engine_parameters={},
                       workflow_params={"missing": "variable"})
    run = manager.prepare_execution(run, files=[])
    manager.database.insert_run(run)
    run = manager.execute(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        stage = run.processing_stage
        if not stage.is_error:
            print("Waiting ... (stage=%s)" % stage.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True

    assert run.execution_log["exit_code"] != 0
    assert not (manager.weskit_context.run_dir(run.sub_dir) / "hello_world.txt").exists()
    assert "hello_world.txt" not in to_filename(run.outputs["filesystem"])

    assert run.execution_log["env"] == {
        "CONDA_ENVS_PATH": "conda_envs/",
        "WESKIT_WORKFLOW_ENGINE": "SMK=7.30.2",
        "WESKIT_WORKFLOW_PATH": str(run.rundir_rel_workflow_path)
    }
    assert run.execution_log["cmd"] == [
        "snakemake",
        "--snakefile",
        str(run.rundir_rel_workflow_path),
        "--cores", "1",
        "--configfile",
        f"{run.id}.yaml"
    ]


@pytest.mark.integration
def test_without_workflow_params_snakemake(manager,
                                           celery_worker):
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2",
                       workflow_engine_parameters={},
                       workflow_params={})
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        stage = run.processing_stage
        if not stage.is_error:
            print("Waiting ... (stage=%s)" % stage.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    # test if workflow submission fails
    assert run.execution_log["exit_code"] != 0
    assert run.execution_log["cmd"] == [
        "snakemake",
        "--snakefile",
        str(run.rundir_rel_workflow_path),
        "--cores", "1",
        '--configfile',
        f"{run.id}.yaml"
        ]


@pytest.mark.integration
def test_execute_nextflow(manager,
                          celery_worker):
    run = get_mock_run(workflow_url="file:wf3/helloworld.nf",
                       workflow_type="NFL",
                       workflow_type_version="23.04.1",
                       workflow_engine_parameters={"trace": "False"})
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    manager.database.insert_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        stage = run.processing_stage
        if stage != ProcessingStage.FINISHED_EXECUTION:
            assert_stage_is_not_failed(stage)
            print("Waiting ... (stage=%s)" % stage.name)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True
    assert run.run_dir(manager.weskit_context) / "hello_world.txt"
    hello_world_files = list(filter(lambda name: os.path.basename(name) == "hello_world.txt",
                                    run.outputs["filesystem"]))
    assert len(hello_world_files) == 2, hello_world_files   # 1 actual file + 1 publish symlink
    with open(run.run_dir(manager.weskit_context) / hello_world_files[0], "r") as fh:
        assert fh.readlines() == ["hello_world\n"]

    assert run.execution_log["env"] == {
        "NXF_OPTS": "-Xmx256m",
        "WESKIT_WORKFLOW_ENGINE": "NFL=23.04.1",
        "WESKIT_WORKFLOW_PATH":  str(run.rundir_rel_workflow_path),
    }
    assert run.execution_log["cmd"] == [
        "nextflow",
        "-Djava.io.tmpdir=/tmp",
        "run",
        str(run.rundir_rel_workflow_path),
        "-params-file", f"{run.id}.yaml",
        "-with-timeline",
        "-with-dag",
        "-with-report",
        "-w",
        "./"
    ]


# Celery's revoke function applied to the Snakemake job results in a change
# of the main process's working directory, if a celery_session_worker is
# used. Therefore, the test should use a celery_worker. THIS does NOT solve
# the general problem though, if in production workers are reused for new
# tasks!
@pytest.mark.skip
def test_cancel_workflow(manager, celery_worker):
    run = get_mock_run(workflow_url="wf2/Snakefile",
                       workflow_type="SMK")
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    # Before we cancel, we need to wait that the execution actually started.
    # Cancellation of the preparation is not implemented.
    time.sleep(5)
    manager.cancel(run)
    assert run.run_stage == ProcessingStage.CANCELED


@pytest.mark.integration
def test_update_all_runs(manager,
                         celery_worker):
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    run = manager.database.update_run(run)

    start_time = time.time()
    success = False
    while not success:
        assert is_within_timeout(start_time), "Test timed out"
        stage = run.processing_stage
        print("Waiting ... (status=%s)" % stage.name)
        if stage != ProcessingStage.FINISHED_EXECUTION:
            assert_stage_is_not_failed(stage)
            time.sleep(1)
            run = manager.update_run(run)
        else:
            success = True

    manager.update_runs()
    db_run = manager.get_run(run.id)
    assert db_run is not None
    assert db_run.processing_stage == ProcessingStage.FINISHED_EXECUTION


@pytest.mark.integration
def test_missing_celery_id(manager):
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    run = manager.database.update_run(run)
    run.processing_stage = ProcessingStage.REQUESTED_CANCEL
    run.celery_task_id = None
    run = manager.update_run(run)
    assert run.processing_stage == ProcessingStage.SYSTEM_ERROR


@pytest.mark.integration
def test_run_id_existence(manager):
    run = get_mock_run(workflow_url="file:wf1/Snakefile",
                       workflow_type="SMK",
                       workflow_type_version="7.30.2")
    manager.database.insert_run(run)
    run = manager.prepare_execution(run, files=[])
    run = manager.execute(run)
    run = manager.database.update_run(run)
    run_id = str("12345678123456781234567812345678")
    run_list = manager.update_runs(run_id)
    # run_id is not an actual run
    # and thus has no databse entry
    assert run_list == []
