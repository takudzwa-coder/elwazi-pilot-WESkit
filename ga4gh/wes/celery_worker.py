from ga4gh.wes import celery
from ga4gh.wes.tasks import run_snakemake  # noqa: F401
import os


celery_config = dict()
celery_config["broker_url"] = os.environ["BROKER_URL"]
celery_config["result_backend"] = os.environ["RESULT_BACKEND"]
celery.conf.update(celery_config)
