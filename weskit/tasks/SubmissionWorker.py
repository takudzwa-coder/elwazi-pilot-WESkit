# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import os
from abc import ABCMeta
from datetime import datetime
from typing import Any
from celery import Task
from werkzeug.utils import cached_property

from weskit.celery_app import celery_app, read_config, update_celery_config_from_env
from weskit.classes.PathContext import PathContext
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.Executor import ExecutionSettings
from weskit.classes.EngineExecutor import get_executor, EngineExecutorType
from weskit.classes.executor2.ProcessId import WESkitExecutionId

logger = logging.getLogger(__name__)


class CommandTask(Task, metaclass=ABCMeta):
    """
    Process-global state for all run_command tasks. Use this for sockets and network connections,
    etc. This allows sharing resources between tasks:

    - SSH connection
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

    # get_executor needs to be adjusted in the future
    @cached_property
    def executor(self) -> Any:
        return get_executor(self.executor_type,
                            login_parameters=self.config["executor"]["login"]
                            if self.executor_type.needs_login_credentials
                            else None,
                            event_loop=None)


@celery_app.task(base=CommandTask)
def run_command(command: ShellCommand,
                execution_settings: ExecutionSettings,
                worker_context: PathContext,
                executor_context: PathContext,
                executor: Any):

    start_time = datetime.now()

    if command.workdir is None:
        raise RuntimeError(f"No working directory defined for command: {command}")
    else:
        workdir = command.workdir

    if run_command.executor_type.executes_engine_remotely:
        logger.info(
            f"Running command in {worker_context.run_dir(workdir)} (worker) = "
            f"{executor_context.run_dir(workdir)} (executor): {repr(command.command)}"
        )
    else:
        if worker_context != executor_context:
            raise RuntimeError(
                f"No remote, but distinct remote path context: {worker_context} "
                f"!= {executor_context}"
            )
        logger.info(
            f"Running command in {executor_context.run_dir(workdir)} (worker): "
            f"{repr(command.command)}"
        )

    shell_command = ShellCommand(
        command=command.command,
        workdir=executor_context.workdir(workdir),
        environment=command.environment
    )

    try:
        log_dir = worker_context.log_dir(workdir, start_time)
        logger.info(f"Creating log-dir {log_dir}")
        os.makedirs(log_dir)
        if run_command.executor_type.executes_engine_locally or \
           run_command.config["executor"]["login"]["hostname"] == "localhost":
            shell_command.environment = {**dict(os.environ), **shell_command.environment}
        else:
            pass

        if executor is None:
            executor = run_command.executor

        process = executor.execute(
            execution_id=WESkitExecutionId,
            command=shell_command,
            stdout_file=executor_context.stdout_file(workdir, start_time),
            stderr_file=executor_context.stderr_file(workdir, start_time),
            settings=execution_settings
        )
        return process
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise
