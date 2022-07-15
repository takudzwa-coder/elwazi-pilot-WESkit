#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import math
from datetime import timedelta
from os import PathLike
from typing import List, Optional, Dict, Union

from weskit.classes.ShellCommand import ShellCommand, ShellSpecial
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.classes.executor.cluster.ClusterExecutor import CommandSet
from weskit.memory_units import Unit, Memory

logger = logging.getLogger(__name__)


class SlurmCommandSet(CommandSet):

    def _environment_parameters(self, environment: Dict[str, str]) -> List[str]:
        """
        Create an `-env` parameter value that exports all requested environment variables to the
        job, but not the environment local to the submission host.
        """

        def quote_comma_value(variable_value: str):
            if variable_value.find(',') != -1:
                # The [docs](https://slurm.schedmd.com/sbatch.html) do not
                # tell what to do, if the value contains both a command and an apostrophe :-(
                return f"'{variable_value}'"
            else:
                return variable_value

        environment_string = "--export=NONE"
        if len(environment) > 0:
            environment_string = "--export="
            # Note: A space after the comma is not allowed.
            # SLURM is able to export ALL|NONE|ALL,<selected varibale>  variables.
            # Variable need to be in finilized form, e.g. ALL,EDITOR=bin/emacs or
            # e.g. EDITOR=bin/emacs
            environment_string += ",".join(
                [f"{it[0]}={quote_comma_value(it[1])}" for it in environment.items()]
            )
        return [environment_string]

    def _logging_parameters(self,
                            stdout_file: Optional[PathLike] = None,
                            stderr_file: Optional[PathLike] = None)\
            -> List[str]:
        """
        Write output to separate or identical stdout and stderr files.
        The default names are %j.out. Error and Output are combined.
        """
        result = []
        if stdout_file is not None:
            result += ["-o", str(stdout_file)]
        if stderr_file is not None:
            result += ["-e", str(stderr_file)]
        if stdout_file is None and stderr_file is None:
            # If no logging is set then redirect to /dev/null
            result += ["-o", "/dev/null"]
        return result

    def _memory_string(self, memory: Memory) -> str:
        """"
        For simplicity's sake, express all memory values in kilobytes. SLURM uses the single-letter
        unit specification 'K' for this and [M|G|T] for the others. Smaller values are rounded up,
        because the string is used for reserving memory and its fine to reserve more.
        """
        return f"{math.ceil(memory.to(Unit.KILO, decimal_multiples=False).value)}K"

    def _walltime_string(self, walltime: timedelta) -> str:
        """
        Return a string representation of a time interval for SLURM. The hours are at least two
        digits, optionally will leading zeros, but may also increase beyond 24 hours.
        Acceptable time formats include "minutes", "minutes:seconds", "hours:minutes:seconds",
        "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".
        """
        hours, without_hours = divmod(walltime.total_seconds(), 3600)
        minutes, seconds = divmod(without_hours, 60)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def submit(self,
               command: ShellCommand,
               stdout_file: Optional[PathLike] = None,
               stderr_file: Optional[PathLike] = None,
               # stdin_file: Optional[PathLike] = None,  # possible with `-i`, but not needed
               settings: Optional[ExecutionSettings] = None) -> ShellCommand:
        """
        Create a sbatch command line for submitting a command to a cluster node. Note that the
        submission command includes the remote working directory and the environment of the
        command. Since srun is interactive and waits for the job to be commlete, we submit jobs
        via sbatch -> sbatch [options] script. Therefore the script needs to be uploaded beforehand.

        If you need shell expansion on the compute node, e.g. that some local variable on there
        is used (e.g. Slurm variables that are only available during execution), then you need
        to wrap the actual command in a shell, e.g.

           command = ["bash", "-c", "echo \"$someVar\""]
           environment = { "someVar": "Hello, World" }

        will evaluate to `echo "Hello, World"`
        """

        # Ensure the job exits, if the working directory does not exist.
        result: List[Union[str, ShellSpecial]] = ["sbatch"]
        result += self._environment_parameters(command.environment)
        result += ["-D", str(command.workdir)] \
            if command.workdir is not None else []
        result += self._logging_parameters(stdout_file, stderr_file)

        if settings is not None:
            result += ["-J", settings.job_name] \
                if settings.job_name is not None else []
            result += ["-a", settings.accounting_name] \
                if settings.accounting_name is not None else []

            result += ["--mem", self._memory_string(settings.memory)] \
                if settings.memory is not None else []

            result += ["-t", self._walltime_string(settings.walltime)] \
                if settings.walltime is not None else []

            result += ["-p", settings.queue] \
                if settings.queue is not None else []

            result += ["-c", str(settings.cores)] \
                if settings.cores is not None else []

        # We always use a single host. Number of Nodes assigned to the job
        result += ["-N", "1"]
        result += [command.command_expression]
        return ShellCommand(result)

    def get_status(self, job_ids: List[str]) -> ShellCommand:
        """
        Get a command that lists the Slurm job states for the requested jobs. The command produces
        on standard output one line for each requested job ID, with two whitespace-separated
        columns, the first being the job ID, the second the status indicate of the cluster system
        (i.e. "DONE", etc.).
        """
        result: List[Union[str, ShellSpecial]] = \
            ["sacct",  "--format=JobID,State,ExitCode", "-j", ",".join(job_ids), "-n", "-X"]
        return ShellCommand(result)

    def kill(self, job_ids: List[str], signal: str = "TERM") -> ShellCommand:
        """
        Get the command to send a termination signal (SIGTERM) to the jobs.
        """
        result: List[Union[str, ShellSpecial]] = ["scancel", "-s", signal]
        result += job_ids
        return ShellCommand(result)

    def wait_for(self, job_id: str) -> ShellCommand:
        """
        A command that blocks, until the requested job ended.
        """
        command: List[Union[str, ShellSpecial]] =\
            ["bash", "-c",
             f"i=\"RUNNING\"; until [ $i != \"RUNNING\" ] &&"
             f"[ $i != \"PENDING\" ] ; do sleep 5; "
             f"i=$(sacct --format=State -j {job_id} -n -X ); done"]
        return ShellCommand(command)
