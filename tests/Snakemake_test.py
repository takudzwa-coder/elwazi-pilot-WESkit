import json, yaml, sys, time

with open("tests/wf1/config.yaml") as file:
  wf1_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

wf1_data = {
  "workflow_params": wf1_params,
  "workflow_type": "Snakemake",
  "workflow_type_version": "5.8.2",
  "workflow_url": "tests/wf1/Snakefile"
}

def test_execute(database_connection, snakemake, celery_worker):
    run = database_connection.create_new_run(request=wf1_data)
    snakemake.execute(run, database_connection)
    running = True
    while running:
        time.sleep(1)
        status = snakemake.get_state(run, database_connection)
        print(status, file=sys.stderr)
        if (status == "COMPLETE"):
            running = False
