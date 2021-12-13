#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import re
from contextlib import contextmanager
from datetime import datetime
from io import IOBase
from os import PathLike
from pathlib import PurePath
from tempfile import NamedTemporaryFile
from typing import Optional, List

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import \
    Executor, ExecutedProcess, RunStatus, CommandResult, ProcessId, ExecutionSettings
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.executor.cluster.lsf.LsfCommandSet import LsfCommandSet

logger = logging.getLogger(__name__)


@contextmanager
def execute(executor: Executor,
            command: ShellCommand,
            encoding="utf-8",
            **kwargs) \
        -> (CommandResult, IOBase, IOBase):
    """
    Convenience syntax for executing a ShellCommand with temporary locally buffered stdout and
    stderr. This is mostly a workaround for dysfunctional data streaming if IOBase objects, in
    particular StringIO or ByteIO, are used. The context will create temporary files and delete
    them on exiting the context. The context executes the command synchronously (i.e. it calls
    `executor.wait_for(process)`.
    """
    with NamedTemporaryFile(encoding=encoding, mode="r") as stdout:
        with NamedTemporaryFile(encoding=encoding, mode="r") as stderr:
            proc = executor.execute(command,
                                    stdout_file=PurePath(stdout.name),
                                    stderr_file=PurePath(stderr.name),
                                    **kwargs)
            result = executor.wait_for(proc)
            yield result, stdout, stderr


class LsfExecutor(Executor):
    """
    Execute LSF job-management operations via shell commands issued on a local/remote host.
    """

    def __init__(self, executor: Executor):
        """
        Provide an executor that is used to execute the cluster commands. E.g. if this the commands
        should run locally, you can use a command_executor.LocalExecutor. If you need to submit via
        a remote connection you can use an command_executor.SshExecutor.
        """
        self._command_set = LsfCommandSet()
        self._executor = executor

    @property
    def executor(self) -> Executor:
        return self._executor

    def extract_jobid_from_bsub(self, stdout: List[str]) -> str:
        if len(stdout) == 0:
            raise ExecutorException("No parsable output during job submission")
        # Sometimes job submission may be delayed, because the LSF cluster is overloaded.
        # I this situation a number of diagnostic messages are shown, but eventually, the
        # submission line is displayed. We simply try to parse all these lines and are happy
        # with the first line that matches.
        matches = map(lambda l: re.match(r"Job <(\d+)> is submitted to .+.\n", l),
                      stdout)
        first_match = next(filter(lambda m: bool(m), matches), None)
        if first_match is None:
            raise ExecutorException(f"Could not parse job ID from: {stdout}")
        return first_match.group(1)

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None) -> ExecutedProcess:
        """
        stdout, stderr, and stdin files are *remote files on the cluster nodes*.

        WARNING: Do not set too many environment variables in `command.environment`. The
                 implementation uses `bsub -env` and too many variables may result in a too long
                 command-line.
        """

        if stdin_file is not None:
            logger.error("stdin_file is not supported in LSFExecutor.execute()")
        # Note that there are at two shell involved: The environment on the submission host
        # and the environment on the compute node, on which the actual command is executed.
        submission_command = ShellCommand(self._command_set.submit(command=command,
                                                                   stdout_file=stdout_file,
                                                                   stderr_file=stderr_file,
                                                                   settings=settings))
        # The actual submission via `bsub` or similar is done quickly. We wait here for the
        # result and then use the cluster job ID returned from the submission command, as process
        # ID to query the cluster job status later.

        with execute(self._executor, submission_command) as (result, stdout, stderr):
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()
            start_time = datetime.now()
            if result.status.failed:
                raise ExecutorException(f"Failed to submit cluster job: {result}" +
                                        f"stdout={stdout_lines}, " +
                                        f"stderr={stderr_lines}")
            else:
                cluster_job_id = ProcessId(self.extract_jobid_from_bsub(stdout_lines))

        logger.debug(f"Cluster job ID {cluster_job_id}: {submission_command}")

        # NOTE: We could now created an additional `bwait` process that waits for the cluster job
        #       ID. However, we postpone the creation of this to a later stage. The process handle
        #       is just the cluster job ID.
        return ExecutedProcess(executor=self,
                               process_handle=cluster_job_id,
                               pre_result=CommandResult(command=command,
                                                        id=cluster_job_id,
                                                        stderr_file=stderr_file,
                                                        stdout_file=stdout_file,
                                                        stdin_file=stdin_file,
                                                        run_status=RunStatus(None),
                                                        start_time=start_time))

    def get_status(self, process: ExecutedProcess) -> RunStatus:
        status_command = ShellCommand(self._command_set.get_status([process.id.value]))
        with execute(self._executor, status_command) as (result, stdout, stderr):
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()

            # bjobs may produce multiple lines output, if it has to wait for the LSF server
            # to answer. We assume that we are only interested in those lines matching the
            # regular expression
            match_lines = list(filter(lambda m: bool(m),
                                      map(lambda line: re.match(r"(\d+)\s+(\S+)\s+(-|\d+)",
                                                                line.rstrip()),
                                          stdout_lines)))
            if len(match_lines) != 1:
                raise ExecutorException(f"No unique match of status for {process.result.id}: " +
                                        f"{str(result)}, " +
                                        f"stdout={stdout_lines}, " +
                                        f"stderr={stderr_lines}")

            # Now get the information about the job executed on the cluster.
            job_id, status_name, reported_exit_code = \
                match_lines[0][1], match_lines[0][2], match_lines[0][3]
            if job_id != str(process.id.value):
                raise ExecutorException("Job ID in parsed bjobs didn't match " +
                                        f"{process.result.id}: " +
                                        f"{str(status_command)}, " +
                                        f"stdout={stdout_lines}, " +
                                        f"stderr={stderr_lines}")

            # The reported exit code is '-' if the job is still running, or if the job
            # is done with return value 0.
            if reported_exit_code == "-":
                if status_name == "DONE":
                    exit_code = 0
                else:
                    exit_code = None
            else:
                exit_code = int(reported_exit_code)

            return RunStatus(exit_code, status_name)

    def kill(self, process: ExecutedProcess):
        # Not tested therefore
        raise NotImplementedError("kill on LsfExecutor is not tested")
        kill_command = ShellCommand(self._command_set.kill(process.id.value))
        self._executor.wait_for(self._executor.execute(kill_command))

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        old_status = process.result.status
        process.result.status = self.get_status(process)
        if old_status.code is None:
            # The status is changed. We avoid having to parse the finishing time of the job (we
            # could use `bjobs -o "finish_time"), because it is complex and configurable. See
            # e.g. the code in BatchEuphoria (https://tinyurl.com/27x44ndb). The following is the
            # cheap solution and sufficient for us, because we always call wait_for().
            process.result.end_time = datetime.now()
        return process

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        wait_command = ShellCommand(self._command_set.wait_for(process.id.value))
        with execute(self._executor, wait_command) as (result, stdout, stderr):
            if result.status.code == 2:
                error_message = stderr.readlines()
                if error_message != \
                        [f"done({process.id.value}): Wait condition is never satisfied\n"]:
                    raise ExecutorException(f"Wait failed: {str(result)}, " +
                                            f"stderr={error_message}, " +
                                            f"stdout={stdout.readlines()}")
            elif result.status.failed:
                raise ExecutorException(f"Wait failed: {str(result)}, " +
                                        f"stderr={stdout.readlines()}, " +
                                        f"stdout={stdout.readlines()}")
        return self.update_process(process).result
