# tests.py
from ga4gh.wes.tasks import mul, long_task, run_snakemake
# celery_worker
#from celery import shared_task
import time

def test_celery_raw_fixtures(celery_app, celery_worker):
    assert mul.delay(4, 4).get(timeout=10) == 16

def test_celery_run_snakemaks(celery_app, celery_worker):
    task = run_snakemake.apply_async(args=["tests/wf1/Snakefile", "tests/wf1"])
    running=True
    while running:
        time.sleep(1)
        running_task = long_task.AsyncResult(task.id)
        if (running_task.state=="SUCCESS"): running=False
    assert running_task.info