import json, yaml, sys, time


def test_execute_snakemake_workflow(database_connection, snakemake, celery_worker, snakemake_wf1_data):
    run = database_connection.create_new_run(request=snakemake_wf1_data)
    snakemake.execute(run, database_connection)
    running = True
    while running:
        time.sleep(1)
        status = snakemake.get_state(run, database_connection)
        print(status, file=sys.stderr)
        if (status == "COMPLETE"):
            running = False

def test_cancel_snakemake_workflow(database_connection, snakemake, celery_worker, snakemake_wf2_data):
    run = database_connection.create_new_run(request=snakemake_wf2_data)
    snakemake.execute(run, database_connection)
    snakemake.cancel(run, database_connection)
    assert snakemake.get_state(run, database_connection) == "CANCELED"