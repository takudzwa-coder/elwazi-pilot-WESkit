# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import weskit.celery_app
from weskit.celery_app import update_celery_config_from_env

update_celery_config_from_env()

celery_app = weskit.celery_app.celery_app

# A start script to be used when starting workers.
