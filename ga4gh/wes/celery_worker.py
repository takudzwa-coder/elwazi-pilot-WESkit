from ga4gh.wes import celery
from ga4gh.wes.wesnake import create_connexion_app
from ga4gh.wes.celery_utils import init_celery

celery_config = dict()
celery_config["broker_url"] = "redis://result_broker:6379"
celery_config["result_backend"] = "redis://result_broker:6379"
celery.conf.update(celery_config)
