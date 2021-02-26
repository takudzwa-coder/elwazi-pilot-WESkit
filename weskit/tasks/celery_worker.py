from weskit.tasks.celery import celery_app
from weskit.tasks.workflow import run_workflow
from weskit.classes.Workflow import Snakemake, Nextflow
import os


celery_config = dict()
celery_config["broker_url"] = os.environ["BROKER_URL"]
celery_config["result_backend"] = os.environ["RESULT_BACKEND"]
celery_app.conf.update(celery_config)
