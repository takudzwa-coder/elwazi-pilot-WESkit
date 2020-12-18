import json, yaml, sys, time, uuid, os
from wesnake.classes.RunStatus import RunStatus
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict

def get_mock_run(workflow_url):
    run = {
        "run_id": str(uuid.uuid4()),
        "run_status": RunStatus.UNKNOWN.encode(),
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
    }
    return run


def test_prepare_execution(snakemake):
    
    # 1.) use workflow on server
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    assert run["run_status"] == RunStatus.INITIALIZING.encode()

    # 2.) workflow does not exist on server -> error message outputs execution
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Filesnake"))
    run = snakemake.prepare_execution(run, files=[])
    assert run["run_status"] == RunStatus.SYSTEM_ERROR.encode()
    assert os.path.isfile(run["outputs"]["execution"])

    # 3.) copy attached workflow to workdir
    wf_url = "wf_1.smk"
    with open(os.path.join(os.getcwd(), "tests/wf1/Snakefile"), "rb") as fp:
        wf_file = FileStorage(fp, filename=wf_url)
        files = ImmutableMultiDict({"workflow_attachment":[wf_file]})
        run = get_mock_run(workflow_url=wf_url)
        run = snakemake.prepare_execution(run, files)
    assert run["run_status"] == RunStatus.INITIALIZING.encode()
    assert os.path.isfile(os.path.join(run["execution_path"], wf_url))

    # 4.) workflow is not attached -> error message outputs execution
    run = get_mock_run(workflow_url="tests/wf1/Snakefile")
    run = snakemake.prepare_execution(run, files=[])
    assert run["run_status"] == RunStatus.SYSTEM_ERROR.encode()
    assert os.path.isfile(run["outputs"]["execution"])

def test_execute_snakemake_workflow(snakemake, celery_worker):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf1/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    run = snakemake.execute(run)
    running = True
    while running:
        time.sleep(1)
        status = snakemake.get_state(run)
        if (status == "COMPLETE"):
            running = False
    assert run["run_status"] == RunStatus.COMPLETE.encode()

def test_cancel_snakemake_workflow(snakemake, celery_worker):
    run = get_mock_run(workflow_url=os.path.join(os.getcwd(), "tests/wf2/Snakefile"))
    run = snakemake.prepare_execution(run, files=[])
    run = snakemake.execute(run)
    snakemake.cancel(run)
    assert run["run_status"] == RunStatus.CANCELED.encode()
