# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from weskit import create_database, create_app
from weskit.celery_app import celery_app, update_celery_config_from_env


def main():
    update_celery_config_from_env()
    app = create_app(celery_app,
                     create_database())
    app.run(host="127.0.0.1", port=5000)
