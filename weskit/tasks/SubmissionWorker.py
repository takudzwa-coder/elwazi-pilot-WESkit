# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
import os
from abc import ABCMeta
from datetime import datetime
from typing import Any
from celery import Task
from pathlib import Path
from uuid import UUID
from werkzeug.utils import cached_property
from functools import wraps

from weskit.classes.Database import Database
from weskit.classes.Run import Run
from weskit.celery_app import celery_app, read_config, update_celery_config_from_env
from weskit.classes.PathContext import PathContext
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.Executor import ExecutionSettings
from weskit.classes.EngineExecutor import get_executor, EngineExecutorType
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.utils import format_timestamp, get_current_timestamp


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
    # it descriminates between the old and the new executor API
    @cached_property
    def executor(self) -> Any:
        return get_executor(self.executor_type,
                            login_parameters=self.config["executor"]["login"]
                            if self.executor_type.needs_login_credentials
                            else None,
                            event_loop=None)

    @cached_property
    def database(self):
        database_url = os.getenv("WESKIT_DATABASE_URL")
        return Database(database_url, "WES")


def custom_run_command(task_func):
    @wraps(task_func)
    def wrapper(*args, **kwargs):
        # Create an instance of CommandTask with executor and database
        command_task_instance = CommandTask()
        command_task_instance.executor = kwargs.pop('executor', None)
        command_task_instance.database = kwargs.pop('database', None)

        # Call the original task function with the modified CommandTask instance
        return task_func(command_task_instance, *args, **kwargs)

    return wrapper


@celery_app.task
@custom_run_command
def run_command(command: ShellCommand,
                execution_settings: ExecutionSettings,
                worker_context: PathContext,
                executor_context: PathContext,
                run_id: UUID,
                executor: Any,
                database: Database):

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

        executor = run_command.executor

        executor.execute(
            execution_id=WESkitExecutionId(),
            command=shell_command,
            stdout_file=executor_context.stdout_file(workdir, start_time),
            stderr_file=executor_context.stderr_file(workdir, start_time),
            settings=execution_settings
        )
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise
    finally:
        # The execution context is the run-directory. It is used to create all paths to be reported
        # relative to the run-directory.
        rundir_context = PathContext(Path("."), Path("."), Path("."))

        # After the submission the job is in the queue. The job is not yet running or finished.
        # Therefore the exit_code is None
        exit_code = None

        execution_log = {
            "start_time": format_timestamp(start_time),
            "cmd": [str(el) for el in command.command],
            "env": command.environment,
            "workdir": str(workdir),
            "end_time": get_current_timestamp(),
            "exit_code": exit_code,
            "stdout_file": str(rundir_context.stdout_file(Path("."), start_time)),
            "stderr_file": str(rundir_context.stderr_file(Path("."), start_time)),
            "log_dir": str(rundir_context.log_dir(Path("."), start_time)),
            "log_file": str(rundir_context.execution_log_file(Path("."), start_time)),
            "output_files": None
        }
        with open(worker_context.execution_log_file(workdir, start_time), "w") as fh:
            json.dump(execution_log, fh)
            print("\n", file=fh)

        database = run_command.database
        run = database.get_run(run_id)
        if run is not None:
            run = database.update_run(run, Run.merge, 1)
            run.execution_log = execution_log
            run = database.update_run(run)

    return execution_log
