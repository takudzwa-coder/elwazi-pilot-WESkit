#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import CommandResult
from weskit.tasks.EngineExecutor import get_executor, EngineExecutorType
from weskit.utils import get_current_timestamp, collect_relative_paths_from, format_timestamp

logger = logging.getLogger(__name__)


class PathContext:

    def __init__(self,
                 base_workdir: Path,
                 run_subdir: Path,
                 timestamp: datetime,
                 log_base_subdir: Path):
        self.base_workdir = base_workdir
        self.run_subdir = run_subdir
        self.timestamp = timestamp
        self.log_base_subdir = log_base_subdir

    @property
    def run_dir(self) -> Path:
        return self.base_workdir / self.run_subdir

    @property
    def workdir(self) -> Path:
        return self.run_dir

    @property
    def log_dir(self) -> Path:
        return self.run_dir / self.log_base_subdir / format_timestamp(self.timestamp)

    @property
    def stderr_file(self) -> Path:
        return self.log_dir / "stderr"

    @property
    def stdout_file(self) -> Path:
        return self.log_dir / "stdout"

    @property
    def execution_log_file(self) -> Path:
        return self.log_dir / "log.json"

    def relocate(self, new_basedir: Path) -> PathContext:
        return PathContext(base_workdir=new_basedir,
                           run_subdir=self.run_subdir,
                           timestamp=self.timestamp,
                           log_base_subdir=self.log_base_subdir)


def run_command(command: List[str],
                local_base_workdir: str,
                sub_workdir: str,
                executor_parameters: Dict[str, Any],
                environment: Optional[Dict[str, str]] = None,
                log_base_subdir: str = ".weskit"):
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

    "exit_code" is set to -1, if no result could be produced from the command, e.g. if a prior
    mkdir failed, or similar abnormal situations.

    TODO: Simplify interface by using object de/serialization.
    """
    if environment is None:
        environment = {}

    start_time = datetime.now()

    # The worker context is used for accessing files locally, e.g. from within the worker container.
    worker_context = PathContext(Path(local_base_workdir),
                                 Path(sub_workdir),
                                 start_time,
                                 Path(log_base_subdir))

    executor_type = EngineExecutorType.from_string(executor_parameters["type"])
    executor = get_executor(executor_type,
                            login_parameters=executor_parameters.get("login", {}))

    # The command context is the context needed by the command, which may be locally or remotely
    # dependent on the executor type.
    command_context: PathContext
    if executor_type.executes_engine_remotely:
        command_context = worker_context.relocate(Path(executor_parameters["remote_base_dir"]))
        logger.info("Running command in {} (worker)/{} (command): {}".
                    format(worker_context.run_dir, command_context.run_dir, command))
    else:
        command_context = worker_context
        logger.info("Running command in {} (worker): {}".
                    format(command_context.run_dir, command))

    shell_command = ShellCommand(command=command,
                                 workdir=command_context.workdir,
                                 environment={})

    result: Optional[CommandResult] = None
    try:
        logger.info("Creating log-dir %s" % str(worker_context.log_dir))
        os.makedirs(worker_context.log_dir)
        if executor_type.executes_engine_locally or \
           executor_parameters["login"]["hostname"] == "localhost":
            # A locally executing engine needs the local environment, e.g. for Conda.
            shell_command.environment = {**dict(os.environ), **environment}
        else:
            # When executing remotely, copying the container-local environment does not make sense,
            # but the environment variables explicitly requested as run_command parameters are
            # needed.
            shell_command.environment = {**environment}

        process = executor.execute(shell_command,
                                   command_context.stdout_file,
                                   command_context.stderr_file)
        result = executor.wait_for(process)

    finally:
        # The relative directory context is used for reporting in the logs.
        relative_context = PathContext(Path("."),
                                       Path("."),
                                       start_time,
                                       Path(log_base_subdir))

        # Collect files, but ignore those, that are in the .weskit/ directory. They are tracked by
        # the fields in the execution log (or that of previous runs in this directory).
        outputs = \
            list(filter(lambda fn: not Path(fn).is_relative_to(worker_context.log_base_subdir),  # type: ignore  # noqa
                        collect_relative_paths_from(worker_context.workdir)))                    # type: ignore  # noqa
        exit_code: Optional[int]
        if result is None:
            # result may be None, if the execution failed because the command does not exist
            exit_code = -1
        else:
            # result.status should not be None, unless the process did not finish, which would be
            # a bug at this place.
            exit_code = result.status.code
        execution_log = {
            "start_time": format_timestamp(start_time),
            "cmd": command,
            "env": environment,
            "workdir": str(worker_context.run_subdir),
            "end_time": get_current_timestamp(),
            "exit_code": exit_code,
            "stdout_file": str(relative_context.stdout_file),
            "stderr_file": str(relative_context.stderr_file),
            "log_dir": str(relative_context.log_dir),
            "log_file": str(relative_context.execution_log_file),
            "output_files": outputs
        }
        with open(worker_context.execution_log_file, "w") as fh:
            json.dump(execution_log, fh)
            print("\n", file=fh)

    return execution_log
