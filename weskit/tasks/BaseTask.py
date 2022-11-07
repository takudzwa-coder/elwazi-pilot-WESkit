#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import logging
from abc import ABCMeta
from typing import Dict

from celery import Task
from werkzeug.utils import cached_property

from weskit.celery_app import update_celery_config_from_env, read_config
from weskit.classes.Database import Database
from weskit.classes.EngineExecutor import get_executor
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.PathContext import PathContext
from weskit.classes.WorkflowEngine import WorkflowEngine
from weskit.classes.WorkflowEngineFactory import WorkflowEngineFactory
from weskit.classes.executor.Executor import Executor
from weskit.globals import container_context, create_database

logger = logging.getLogger(__name__)


class BaseTask(Task, metaclass=ABCMeta):
    """
    Process-global state for all run_workflow tasks. Use this for sockets and network connections,
    etc. This allows to share resources between tasks:

    - SSH connection
    - asyncio event-loop
    - database connection

    See https://celery-safwan.readthedocs.io/en/latest/userguide/tasks.html#instantiation
    """

    @cached_property
    def config(self):
        config = read_config()
        update_celery_config_from_env()
        return config

    @cached_property
    def executor_type(self) -> EngineExecutorType:
        return EngineExecutorType.from_string(self.config["executor"]["type"])

    @cached_property
    def worker_context(self) -> PathContext:
        return container_context()

    @cached_property
    def executor_context(self) -> PathContext:
        executor_type = EngineExecutorType.from_string(self.config["executor"]["type"])
        if executor_type.needs_login_credentials:
            return PathContext(base_url=???,
                               data_dir=self.config["executor"]["remote_data_dir"],
                               workflows_dir=self.config["executor"]["remote_workflows_dir"])
        else:
            return self.worker_context

    @cached_property
    def executor(self) -> Executor:
        return get_executor(self.executor_type,
                            login_parameters=self.config["executor"]["login"]
                            if self.executor_type.needs_login_credentials else None)

    @cached_property
    def database(self) -> Database:
        return create_database()

    @cached_property
    def workflow_engines(self) -> Dict[str, Dict[str, WorkflowEngine]]:
        return WorkflowEngineFactory.create(self.config["workflow_engines"])
