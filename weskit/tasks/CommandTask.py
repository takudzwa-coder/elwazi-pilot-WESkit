import logging
import os
import pathlib
import subprocess
from typing import List

from weskit.utils import get_current_timestamp, get_relative_file_paths

logger = logging.getLogger(__name__)


def run_command(command: List[str],
                workdir: str):
    """
    Run a command in a working directory. The workflow_type parameter is only used for logging.
    """
    timestamp = get_current_timestamp()

    logger.info("Running command in {}: {}".format(workdir, command))

    with open(os.path.join(workdir, "command"), "a") as commandOut:
        print("{}: {}, workddir={}".format(timestamp, command, workdir),
              file=commandOut, flush=True)

        with open(os.path.join(workdir, "stderr"), "a") as stderr:
            print(timestamp, file=stderr, flush=True)

            with open(os.path.join(workdir, "stdout"), "a") as stdout:
                print(timestamp, file=stdout, flush=True)
                result = \
                    subprocess.run(command,
                                   cwd=str(pathlib.PurePath(workdir)),
                                   stdout=stdout,
                                   stderr=stderr)
        print("{}: exit code = {}".
              format(get_current_timestamp(), result.returncode),
              file=commandOut, flush=True)

    outputs = get_relative_file_paths(workdir)
    return outputs
