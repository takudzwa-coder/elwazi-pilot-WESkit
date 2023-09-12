# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

# Standard layout for larger Celery projects:
# https://celery-safwan.readthedocs.io/en/latest/getting-started/next-steps.html#proj-celery-py
import logging
import os

import yaml
from celery import Celery

import weskit.serializer
import weskit.celeryconfig # noqa F401

logger = logging.getLogger(__name__)


def create_celery(**kwargs):
    broker_url = os.environ.get("BROKER_URL")
    # Provide RESULT_BACKEND as lower-priority variable than the native CELERY_RESULT_BACKEND.
    backend_url = os.environ.get("CELERY_RESULT_BACKEND",
                                 os.environ.get("RESULT_BACKEND"))
    celery = Celery(
        app="WESkit",
        broker=broker_url,
        backend=backend_url)
    celery.config_from_object(weskit.celeryconfig)   # noqa F821
    celery.conf.update(**kwargs)
    return celery


def read_config():
    if os.getenv("WESKIT_CONFIG") is not None:
        config_file = os.getenv("WESKIT_CONFIG", "")
    else:
        raise ValueError("Cannot start WESkit: Environment variable WESKIT_CONFIG is undefined")

    with open(config_file, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        logger.info("Read config from " + config_file)
    return config


def update_celery_config_from_env():
    # Insert the "celery" section from the configuration file into the Celery config.
    # Always start with the static weskit.celeryconfig and add what is found in the
    # weskit.yaml's `celery` block.
    celery_app.config_from_object(weskit.celeryconfig)
    celery_app.conf.update(**read_config().get("celery", {}))


# Initialize the celery application just with the default configs from the weskit.celeryconfig
# module. Later, update_celery_config() can be called
celery_app = create_celery()

# Note: No task registration here. The tasks are registered later by `@celery_app.taks`.
