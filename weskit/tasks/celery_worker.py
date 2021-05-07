#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import weskit
import os
from weskit.tasks.CommandTask import run_command

celery_app = weskit.create_celery(
    os.environ["BROKER_URL"],
    os.environ["RESULT_BACKEND"]
    )

celery_app.task(run_command)
