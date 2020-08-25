from ga4gh.wes.tasks import run_snakemake
import time, sys


def test_celery_run_snakemake(celery_app, celery_worker):
    print("send task",  file=sys.stderr)
    run_kwargs = {
        "snakefile":"tests/wf1/Snakefile",
        "workdir":"tests/wf1",
        "configfiles":["tests/wf1/config.yaml"],
        "cores":2,
        "forceall":True
    }
    task = run_snakemake.apply_async(args = [], kwargs=run_kwargs)
    running=True
    while running:
        time.sleep(1)
        running_task = run_snakemake.AsyncResult(task.id)
        if (running_task.state=="SUCCESS"): running=False
    assert running_task.info
