# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import os
from abc import ABCMeta
from datetime import datetime
from typing import Union, Callable
from celery import Task
from pathlib import Path
from werkzeug.utils import cached_property
from uuid import UUID

from asyncio import AbstractEventLoop
from weskit.classes.Database import Database
from weskit.classes.Run import Run
from weskit.celery_app import celery_app, read_config, update_celery_config_from_env
from weskit.classes.PathContext import PathContext
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.Executor import ExecutionSettings
from weskit.classes.EngineExecutor import get_executor
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.utils import get_event_loop, format_timestamp

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
    def event_loop(self) -> AbstractEventLoop:
        return get_event_loop()

    @cached_property
    def config(self):
        config = read_config()
        update_celery_config_from_env()
        return config

    @cached_property
    def executor_type(self) -> EngineExecutorType:
        return EngineExecutorType.from_string(self.config["executor"]["type"])

    @cached_property
    def executor(self):
        logger.info("Determine executor for celery task")
        return get_executor(self.executor_type,
                            login_parameters=self.config["executor"]["login"]
                            if self.executor_type.needs_login_credentials
                            else None,
                            event_loop=self.event_loop)

    @cached_property
    def database(self):
        logger.info("Get database connection for celery task")
        database_url = os.getenv("WESKIT_DATABASE_URL")
        return Database(database_url, "WES")

    def run_sync(self, async_fun: Callable, *args, **kwargs):
        try:
            state = self.event_loop.run_until_complete(async_fun(*args, **kwargs))
            return state
        except Exception as e:
            logger.error(f"Error in run_sync: {str(e)}")
            raise


async def run_command_impl(task: Task,
                           command: ShellCommand,
                           execution_settings: ExecutionSettings,
                           worker_context: PathContext,
                           executor_context: PathContext,
                           run_id: UUID):

    start_time = datetime.now()
    workdir = command.workdir

    if workdir is None:
        raise RuntimeError(f"No working directory defined for command: {command}")

    if task.executor_type.executes_engine_remotely:
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
        run = task.database.get_run(run_id)
        if isinstance(run, dict):
            run = Run(**dict(run))
        if run is not None:
            execution_id = WESkitExecutionId()
            run.execution_id = execution_id
            run = task.database.update_run(run, Run.merge, 1)

        log_dir = task.executor.log_dir_base
        logger.info(f"Creating log-dir {log_dir}")
        storage = task.executor.storage
        await storage.create_dir(log_dir, exists_ok=False)

        state = await task.executor.execute(
                        execution_id=execution_id,
                        command=shell_command,
                        stdout_file=executor_context.stdout_file(workdir, start_time),
                        stderr_file=executor_context.stderr_file(workdir, start_time),
                        settings=execution_settings
                       )
        print(state)
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        print(f"Exception details: {e}")
        raise
    finally:
        # The execution context is the run-directory. It is used to create all paths to be reported
        # relative to the run-directory.
        rundir_context = PathContext(Path("."), Path("."), Path("."))

        execution_log = {
            "start_time": format_timestamp(start_time),
            "cmd": [str(el) for el in command.command],
            "env": command.environment,
            "workdir": str(workdir),
            "end_time": None,
            "exit_code": None,
            "stdout_file": str(rundir_context.stdout_file(Path("."), start_time)),
            "stderr_file": str(rundir_context.stderr_file(Path("."), start_time)),
            "log_dir": str(rundir_context.log_dir(Path("."), start_time)),
            "log_file": str(rundir_context.execution_log_file(Path("."), start_time)),
            "output_files": None
        }

        # Update run with ExecutionState information
        print(f" State= str({state.name})")
        print(task.executor.hostname)
        state_log = {
            "created_at": format_timestamp(state.created_at),
            "name": state.name,
            "is_closed": state.is_closed,
            "lifetime": str(state.lifetime),
            "executor_name": str(task.executor.hostname)
        }

        try:
            run.execution_log = execution_log
            run.state_log = state_log
            run = task.database.update_run(run, Run.merge, 1)
            logger.info(f"Database updated with execution_log and state_log '{run_id}'")
        except Exception as e:
            logger.error(f"Error during database update: {str(e)}")
            raise


@celery_app.task(base=CommandTask)
async def run_command(command: ShellCommand,
                      execution_settings: ExecutionSettings,
                      worker_context: PathContext,
                      executor_context: PathContext,
                      run_id: Union[UUID, str]
                      ):

    run_command.run_sync(run_command_impl,
                         command,
                         execution_settings,
                         worker_context,
                         executor_context,
                         run_id,)
