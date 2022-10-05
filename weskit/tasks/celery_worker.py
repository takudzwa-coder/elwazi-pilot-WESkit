#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import weskit.serializer
from weskit.tasks.config import read_config

celery_app = weskit.create_celery()
# Insert the "celery" section from the configuration file into the Celery config.
celery_app.conf.update(**read_config().get("celery", {}))

# Note: No task registration here. The tasks are registered later by `@celery_app.taks`.
