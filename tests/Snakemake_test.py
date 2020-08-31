import json
import time
import yaml


def test_snakemake_execute(
        snakemake_executor,
        database_connection,
        celery_app,
        celery_worker):

    test_run_id = "test_workflow_runid"

    with open("tests/wf1/config.yaml") as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "Snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": "tests/wf1/Snakefile"
    }

    run = database_connection.create_new_run(test_run_id, request=data)
    run = snakemake_executor.execute(run, database_connection)
    running = True
    while running:
        time.sleep(1)
        run_state = snakemake_executor.get_state(run)
        if (run_state == "SUCCESS"):
            running = False
        print(run_state)
    assert True
