# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
import os
from abc import ABCMeta
from asyncio import AbstractEventLoop
from datetime import datetime
from pathlib import Path

from celery import Task
from typing import Optional
from werkzeug.utils import cached_property

from weskit.celery_app import celery_app, read_config, update_celery_config_from_env
from weskit.classes.EngineExecutor import get_executor, EngineExecutorType
from weskit.classes.PathContext import PathContext
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import CommandResult, ExecutionSettings, Executor
from weskit.utils import \
    format_timestamp, get_event_loop, get_current_timestamp, collect_relative_paths_from

logger = logging.getLogger(__name__)


class CommandTask(Task, metaclass=ABCMeta):
    """
    Process-global state for all run_command tasks. Use this for sockets and network connections,
    etc. This allows to share resources between tasks:

    - SSH connection
    - asyncio event-loop
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
    def executor(self) -> Executor:
        return get_executor(self.executor_type,
                            login_parameters=self.config["executor"]["login"]
                            if self.executor_type.needs_login_credentials
                            else None,
                            event_loop=self.event_loop)


@celery_app.task(base=CommandTask)
def run_command(command: ShellCommand,
                execution_settings: ExecutionSettings,
                worker_context: PathContext,
                executor_context: PathContext):
    """
    Run a command in a working directory. The sub_workdir has to be a relative path, such that
    `base_workdir/sub_workdir` is the path in which the command is executed. base_workdir
    can be absolute or relative. For relative paths, the path will be in the active directory
    which can be either locally or remotely (e.g. the home directory after SSH login, whatever
    that may be).

    Write log files into a timestamp sub-directory of `sub_workdir/log_base`. There will be
    `stderr` and `stdout` files for the respective output of the command and `log.json` with
    general logging information, including the "command", "start_time", "end_time", and the
    "exit_code". Paths in the execution log are all relative.

    Returns a dict with fields "stdout_file", "stderr_file", "log_file" for the three log
    files, and "output_files" for all files created by the process, except the three log-files.
    All paths in the file will be relative to the base_workdir/sub_workdir (remote or local),
    except for the workdir, which is the relative path beneath the local_base_workdir directory
    (that should be the WESKIT_DATA directory).

    "exit_code" is set to negative values for system errors

      * -1: No result could be produced from the command, e.g. if a prior
            mkdir failed, or similar abnormal situations.
      * -2: The process was waited for without timeout, but no valid exit-code was produced
            (Executor.wait_for() should always result in an exit-code != None).
    """
    start_time = datetime.now()

    # It's a bug to have workdir not defined here!
    if command.workdir is None:
        raise RuntimeError("No working directory defined for command: %s" % str(command))
    else:
        workdir = command.workdir

    # The command context is the context needed by the command, which may be local or remote,
    # dependent on the executor type.
    if run_command.executor_type.executes_engine_remotely:
        logger.info("Running command in {} (worker) = {} (executor): {}".
                    format(worker_context.run_dir(workdir),
                           executor_context.run_dir(workdir),
                           [repr(el) for el in command.command]))
    else:
        if worker_context != executor_context:
            raise RuntimeError("No remote, but distinct remote path context: "
                               f"{worker_context} != {executor_context}")
        logger.info("Running command in {} (worker): {}".
                    format(executor_context.run_dir(workdir),
                           [repr(el) for el in command.command]))

    # Make a copy of the ShellCommand appropriate for the (possibly remote) executor environment.
    shell_command = ShellCommand(command=command.command,
                                 workdir=executor_context.workdir(workdir),
                                 environment=command.environment)

    result: Optional[CommandResult] = None
    try:
        log_dir = worker_context.log_dir(workdir, start_time)
        logger.info("Creating log-dir %s" % str(log_dir))
        os.makedirs(log_dir)
        if run_command.executor_type.executes_engine_locally or \
           run_command.config["executor"]["login"]["hostname"] == "localhost":
            # A locally executing engine needs the local environment, e.g. for Conda.
            shell_command.environment = {**dict(os.environ), **shell_command.environment}
        else:
            # When executing remotely, copying the container-local environment does not make sense,
            # but the environment variables explicitly requested as run_command parameters are
            # needed.
            pass

        process =\
            run_command.executor.execute(
                shell_command,
                stdout_file=executor_context.stdout_file(workdir, start_time),
                stderr_file=executor_context.stderr_file(workdir, start_time),
                settings=execution_settings)
        result = run_command.executor.wait_for(process)

    finally:
        # The execution context is the run-directory. It is used to create all paths to be reported
        # relative to the run-directory.
        rundir_context = PathContext(Path("."), Path("."))

        # Collect files, but ignore those that are in the .weskit/ directory. They are tracked by
        # the fields in the execution log (or that of previous runs in this directory).
        outputs = \
            list(filter(lambda fn: not Path(fn).is_relative_to(worker_context.log_base_subdir),  # type: ignore  # noqa
                        collect_relative_paths_from(worker_context.workdir(workdir))))   # type: ignore  # noqa
        exit_code: Optional[int]
        if result is None:
            # result may be None, if the execution failed because the command does not exist.
            exit_code = -1
        else:
            exit_code = result.status.code
            if exit_code is None:
                # result.status should not be None if wait_for() was run. Let's not terminate the
                # worker, but just return some exit code value that indicates a system error.
                exit_code = -2
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
            "output_files": outputs
        }
        with open(worker_context.execution_log_file(workdir, start_time), "w") as fh:
            json.dump(execution_log, fh)
            print("\n", file=fh)

    return execution_log
