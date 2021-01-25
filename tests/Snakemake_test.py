import json, yaml, sys, time, uuid, os
from weskit.classes.Run import Run
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict
from test_utils import get_mock_run


def test_prepare_execution(snakemake):
    
    # 1.) use workflow on server
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    assert run.run_status_check("INITIALIZING")

    # 2.) workflow does not exist on server -> error message outputs execution
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Filesnake"))
    run = snakemake.prepare_execution(run, files=[])
    assert run.run_status_check("SYSTEM_ERROR")
    assert os.path.isfile(run.outputs["execution"])

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment":[wf_file]})
        run = get_mock_run(workflow_url=wf_url)
        run = snakemake.prepare_execution(run, files)
    assert run.run_status_check("INITIALIZING")
    assert os.path.isfile(os.path.join(run.execution_path, wf_url))

    # 4.) workflow is not attached -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Snakefile")
    run = snakemake.prepare_execution(run, files=[])
    assert run.run_status_check("SYSTEM_ERROR")
    assert os.path.isfile(run.outputs["execution"])

def test_execute_snakemake_workflow(snakemake, celery_worker):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    run = snakemake.execute(run)
    while not run.run_status_check("COMPLETE"):
        run = snakemake.update_state(run)
        time.sleep(1)
    snakemake.update_outputs(run).outputs
    assert "hello_world.txt" in run.outputs["Snakemake"]

def test_cancel_snakemake_workflow(snakemake, celery_worker):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf2/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    run = snakemake.execute(run)
    snakemake.cancel(run)
    assert run.run_status_check("CANCELED")

def test_update_all_runs(snakemake, celery_worker, database_connection):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    database_connection.insert_run(run)
    run = snakemake.prepare_execution(run, files=[])
    run = snakemake.execute(run)
    database_connection.update_run(run)
    while not run.run_status_check("COMPLETE"):
        time.sleep(1)
        run = snakemake.update_state(run)
    snakemake.update_runs(database_connection, query={})
    db_run = database_connection.get_run(run_id=run.run_id)
    assert db_run.run_status_check("COMPLETE")
