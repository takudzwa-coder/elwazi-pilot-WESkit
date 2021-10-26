#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import shlex
from os import PathLike
from typing import List, Optional, Dict

import math
from datetime import timedelta

from weskit.memory_units import Unit, Memory
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import ExecutionSettings


class LsfCommandSet:

    def _environment_parameters(self, environment: Dict[str, str]) -> List[str]:
        """
        Create an `-env` parameter value that exports all requested environment variables to the
        job, but not the environment local to the submission host.
        """

        def quote_comma_value(variable_value: str):
            if variable_value.find(',') != -1:
                # The [docs](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=o-env) do not
                # tell what to do, if the value contains both a command and an apostrophe :-(
                return f"'{variable_value}'"
            else:
                return variable_value

        if len(environment) == 0:
            environment_string = "none"
        else:
            # Note: The space after the comma is needed.
            environment_string = ", ".join(
                [f"{it[0]}={quote_comma_value(it[1])}" for it in environment.items()]
            )
        return ["-env", environment_string]

    def _logging_parameters(self,
                            stdout_file: Optional[PathLike] = None,
                            stderr_file: Optional[PathLike] = None)\
            -> List[str]:
        """
        Write output to separate or identical stdout and stderr files, but do not try to send an
        email, if no output files are specified, but discard the output. You can use the %J to
        specify that the output file should contain the cluster job ID.
        """
        result = []
        if stdout_file is not None or stderr_file is not None:
            result += ["-oo", str(stdout_file)]
            result += ["-eo", str(stderr_file)]
        else:
            # If no logging is set then by default the logs go out via email. This prevents this.
            result += ["-oo", "/dev/null"]
        return result

    def _memory_string(self, memory: Memory) -> str:
        """"
        For simplicity's sake, express all memory values in kilobytes. LSF uses the single-letter
        unit specification 'K' for this. Smaller values are rounded up, because the string is used
        for reserving memory and its fine to reserve more.
        """
        return f"{math.ceil(memory.to(Unit.KILO, decimal_multiples=False).value)}K"

    def _walltime_string(self, walltime: timedelta) -> str:
        """
        Return a string representation of a time interval for LSF. The hours are at least two
        digits, optionally will leading zeros, but may also increase beyond 24 hours.
        """
        hours, without_hours = divmod(walltime.total_seconds(), 3600)
        minutes, seconds = divmod(without_hours, 60)
        return "%02d:%02d" % (hours, minutes)

    def submit(self,
               command: ShellCommand,
               stdout_file: Optional[PathLike] = None,
               stderr_file: Optional[PathLike] = None,
               # stdin_file: Optional[PathLike] = None,  # possible with `-i`, but not needed
               settings: Optional[ExecutionSettings] = None) -> List[str]:
        """
        Create a bsub command line for submitting an command to a cluster node. Note that the
        submission command includes the remote working directory and the environment of the
        command.

        If you need shell expansion on the compute node, e.g. that some local variable on there
        is used (e.g. LSF variables that are only available during execution), then you need
        to wrap the actual command in a shell, e.g.

           command = ["bash", "-c", "echo \"$someVar\""]
           environment = { "someVar": "Hello, World" }

        will evaluate to `echo "Hello, World"`
        """
        result = ["bsub"]
        result += self._environment_parameters(command.environment)
        result += ["-cwd", str(command.workdir)] \
            if command.workdir is not None else []
        result += self._logging_parameters(stdout_file, stderr_file)

        if settings is not None:
            result += ["-J", settings.job_name] \
                if settings.job_name is not None else []
            result += ["-P", settings.accounting_name] \
                if settings.accounting_name is not None else []

            result += [
                "-M", self._memory_string(settings.total_memory),
                "-R", f"rusage[mem={self._memory_string(settings.total_memory)}]"] \
                if settings.total_memory is not None else []

            result += ["-W", self._walltime_string(settings.walltime)] \
                if settings.walltime is not None else []

            result += ["-G", settings.group] \
                if settings.group is not None else []

            result += ["-q", settings.queue] \
                if settings.queue is not None else []

            result += ["-c", str(settings.cores)] \
                if settings.cores is not None else []

        # We always use a single host.
        result += ["-R", "span[hosts=1]"]

        result += [" ".join(list(map(shlex.quote, command.command)))]
        return result

    def get_status(self, job_ids: List[str]) -> List[str]:
        """
        Get a command that lists the LSF job states for the requested jobs. The command produces
        on standard output one line for each requested job ID, with two whitespace-separated
        columns, the first being the job ID, the second the status indicate of the cluster system
        (i.e. "DONE", etc.).
        """
        # The reason to wrap the command into bash is that it contains a pipe. All command elements
        # are quoted and the command shall be interpreted without a shell, but the '|' is a shell
        # instruction.
        result = ["bash", "-c",
                  "bjobs -o 'jobid stat exit_code' " +
                  " ".join(job_ids) +
                  " | tail -n +2"]
        return result

    def kill(self, job_ids: List[str], signal: str = "TERM") -> List[str]:
        """
        Get the command to send a termination signal (SIGTERM) to the jobs.
        """
        result = ["bkill", "-s", signal] + job_ids
        return result

    def wait_for(self, job_id: str):
        """
        A command that blocks (up to a year), until the requested job ended.
        """
        return ["bwait", "-t", "525600", "-w", f"done({job_id})"]
