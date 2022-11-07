#!/usr/bin/env python

#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from weskit.globals import create_database
from weskit import create_app
from weskit.celery_app import celery_app, update_celery_config_from_env

update_celery_config_from_env()
app = create_app(celery_app,
                 create_database())
