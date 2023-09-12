#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from weskit import create_app, create_database
from weskit.celery_app import celery_app, update_celery_config_from_env

update_celery_config_from_env()
app = create_app(celery_app,
                 create_database())
