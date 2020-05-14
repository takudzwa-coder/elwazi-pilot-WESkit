from ga4gh.wes import celery
from ga4gh.wes.wesnake import create_app, create_database
from ga4gh.wes.celery_utils import init_celery
from ga4gh.wes.tasks import long_task
import sys, os, yaml
from logging.config import dictConfig
import logging



# load config
config_file = "/wesnake/scratch/config.yaml"
with open(config_file, "r") as yaml_file:
        config = yaml.load(yaml_file, Loader=yaml.FullLoader)

# load validation
validation_file  = "/wesnake/config/validation.yaml"
with open(validation_file, "r") as yaml_file:
    validation = yaml.load(yaml_file, Loader=yaml.FullLoader)

# load log_config
log_config_file = "/wesnake/config/log-config.yaml"
with open(log_config_file, "r") as yaml_file:
    log_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
    dictConfig(log_config)
    logger = logging.getLogger("default")

database = create_database(config)
connexion_app = create_app(config, validation, log_config, logger, database)

init_celery(celery, connexion_app.app)