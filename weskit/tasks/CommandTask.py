#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import json
import logging
import os
import pathlib
import subprocess
from typing import List, Optional, Dict

from weskit.utils import get_current_timestamp, collect_relative_paths_from

logger = logging.getLogger(__name__)


def run_command(command: List[str],
                base_workdir: str,
                sub_workdir: str,
                environment: Dict[str, str] = {},
                log_base: str = ".weskit"):
    """
    Run a command in a working directory. The workdir has to be an relative path, such that
    base_workdir/sub_workdir is the absolute path in which the command is executed. base_workdir
    can be absolute or relative.

    Write log files into a timestamp sub-directory of `sub_workdir/log_base`. There will be
    `stderr` and `stdout` files for the respective output of the command and `log.json` with
    general logging information, including the "command", "start_time", "end_time", and the
    "exit_code". Paths in the execution log are all relative.

    Returns a dict with fields "stdout_file", "stderr_file", "log_file" for the three log
    files, and "output_files" for all files created by the process, but not the three log-files.

    "exit_code" is set to -1, if no result could be produced from the command, e.g. if a prior
    mkdir failed, or similar abnormal situations.
    """
    workdir_abs = os.path.join(base_workdir, sub_workdir)
    logger.info("Running command in {}: {}".format(workdir_abs, command))
    start_time = get_current_timestamp()
    log_dir_rel = os.path.join(log_base, start_time)
    stderr_file_rel = os.path.join(log_dir_rel, "stderr")
    stdout_file_rel = os.path.join(log_dir_rel, "stdout")
    execution_log_rel = os.path.join(log_dir_rel, "log.json")
    result: Optional[subprocess.CompletedProcess] = None
    # Let this explicitly inherit the task environment for the moment, e.g. for conda.
    env = {**dict(os.environ), **environment}
    try:
        log_dir_abs = os.path.join(workdir_abs, log_dir_rel)
        stderr_file_abs = os.path.join(workdir_abs, stderr_file_rel)
        stdout_file_abs = os.path.join(workdir_abs, stdout_file_rel)
        os.makedirs(log_dir_abs)
        with open(stderr_file_abs, "a") as stderr:
            with open(stdout_file_abs, "a") as stdout:
                result = \
                    subprocess.run(command,
                                   cwd=str(pathlib.PurePath(workdir_abs)),
                                   stdout=stdout,
                                   stderr=stderr,
                                   env=env)
    finally:
        # Collect files, but ignore those, that are in the .weskit/ directory. They are tracked by
        # the fields in the execution log (or that of previous runs in this directory).
        outputs = list(filter(lambda fn: os.path.commonpath([fn, log_base]) != log_base,
                              collect_relative_paths_from(workdir_abs)))
        execution_log = {
            "start_time": start_time,
            "cmd": command,
            "env": environment,
            "workdir": sub_workdir,
            "end_time": get_current_timestamp(),
            "exit_code": result.returncode if result is not None else -1,
            "stdout_file": stdout_file_rel,
            "stderr_file": stderr_file_rel,
            "log_dir": log_dir_rel,
            "log_file": execution_log_rel,
            "output_files": outputs
        }
        execution_log_abs = os.path.join(workdir_abs, execution_log_rel)
        with open(execution_log_abs, "w") as fh:
            json.dump(execution_log, fh)

    return execution_log
