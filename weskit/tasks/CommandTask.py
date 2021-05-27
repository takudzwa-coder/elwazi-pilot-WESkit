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
                workdir: str,
                env: Dict[str, str] = {},
                log_base: str = ".weskit"):
    """
    Run a command in a working directory.

    Write log files into a timestamp sub-directory of `workdir/log_base`. There will be `stderr`
    and `stdout` files for the respective output of the command and `command.json` with general
    runtime information, including the "command", "start_time", "end_time", and the "exit_code".

    Returns a dict with fields "stdout_file", "stderr_file", "command_file" for the three log
    files, and "output_files" for all files created by the process, but not the three log-files.
    """
    start_time = get_current_timestamp()
    log_dir = os.path.join(workdir, log_base, start_time)
    logger.info("Running command in {}: {}".format(workdir, command))
    stderr_file = os.path.join(log_dir, "stderr")
    stdout_file = os.path.join(log_dir, "stdout")
    command_file = os.path.join(log_dir, "command.json")
    result: Optional[subprocess.CompletedProcess] = None
    try:
        os.makedirs(log_dir)
        with open(stderr_file, "a") as stderr:
            with open(stdout_file, "a") as stdout:
                result = \
                    subprocess.run(command,
                                   cwd=str(pathlib.PurePath(workdir)),
                                   stdout=stdout,
                                   stderr=stderr)
    finally:
        outputs = list(filter(
            lambda fn: fn not in list(
                map(lambda logfile: os.path.relpath(logfile, workdir),
                    [stdout_file, stderr_file, command_file])),
            collect_relative_paths_from(workdir)))
        execution_log = {
            "start_time": start_time,
            "cmd": command,
            "env": env,
            "workdir": workdir,
            "end_time": get_current_timestamp(),
            "exit_code": result.returncode if result is not None else -1,
            "stdout_file": stdout_file,
            "stderr_file": stderr_file,
            "command_file": command_file,
            "output_files": outputs
        }
        with open(command_file, "w") as fh:
            json.dump(execution_log, fh)

    return execution_log
