#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import weskit.celery_app
from weskit.celery_app import update_celery_config_from_env

update_celery_config_from_env()

celery_app = weskit.celery_app.celery_app

# A start script to be used when starting workers.
