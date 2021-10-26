#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import re
from datetime import datetime
from os import PathLike
from pathlib import PurePath
from tempfile import NamedTemporaryFile
from typing import Optional, List

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import \
    Executor, ExecutedProcess, RunStatus, CommandResult, ProcessId
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.executor.cluster.ExecutionSettings import ClusterExecutionSettings
from weskit.classes.executor.cluster.lsf.LsfCommandSet import LsfCommandSet

logger = logging.getLogger(__name__)


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

    def _parse_submission_stdout(self, stdout: List[str]) -> str:
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
                settings: Optional[ClusterExecutionSettings] = None) -> ExecutedProcess:
        """
        stdout, stderr, and stdin files are *remote files on the cluster nodes*.
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

        # Note: Unfortunately, the StringIO behavior is odd (loss of getvalue() after close!)
        #       and even if that is fixed, asyncssh.create_process, used in the SshExecutor,
        #       does no produce the output in the StringIO for stdout. So, let's use temporary
        #       files.
        with NamedTemporaryFile(encoding="utf-8", mode="r") as subm_stdout:
            with NamedTemporaryFile(encoding="utf-8", mode="r") as subm_stderr:
                # We open the tempfiles "r" and use just their names for writing to them in the
                # executor.
                process = self._executor.execute(submission_command,
                                                 stdout_file=PurePath(subm_stdout.name),
                                                 stderr_file=PurePath(subm_stderr.name),
                                                 encoding="utf-8")
                submission_result = self._executor.wait_for(process)
                stdout = subm_stdout.readlines()
                stderr = subm_stderr.readlines()
        start_time = datetime.now()
        if submission_result.status.failed:
            raise ExecutorException(f"Failed to submit cluster job: {submission_result}" +
                                    f"stdout={stdout}, " +
                                    f"stderr={stderr}")
        else:
            cluster_job_id = ProcessId(self._parse_submission_stdout(stdout))

        # NOTE: We could here created an additional `bwait` process that waits for the cluster job
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
        # The same trick as in execute: Create readable tempfiles, but provide them to asyncssh
        # by name, such that the open readably filehandle remains open and can be used.
        with NamedTemporaryFile(encoding="utf-8", mode="r") as stdout:
            with NamedTemporaryFile(encoding="utf-8", mode="r") as stderr:
                status_command = ShellCommand(self._command_set.get_status([process.id.value]))
                proc = self._executor.execute(status_command,
                                              stdout_file=PurePath(stdout.name),
                                              stderr_file=PurePath(stderr.name),
                                              encoding="utf-8")
                # Ensure the bjobs command succeeded.
                result = self._executor.wait_for(proc)
                stdout_lines = stdout.readlines()
                stderr_lines = stderr.readlines()
                if result.status.failed or len(stdout_lines) != 1:
                    raise ExecutorException(f"Failure status request: {str(result)}, " +
                                            f"stdout={stdout_lines}, " +
                                            f"stderr={stderr_lines}")

                # Now get the information about the job executed on the cluster.
                job_id, status_name, reported_exit_code = \
                    re.split(r"\s+", stdout_lines[0].rstrip())
                if job_id != str(process.id.value):
                    raise ExecutorException(f"Error in bjobs output of {str(status_command)}, " +
                                            f"stdout={stdout_lines}, " +
                                            f"stderr={stderr_lines}")

                # The reported exit code is '-' if the job is still running, or if the job
                # is done with return value 0.
                exit_code = reported_exit_code
                if reported_exit_code == "-":
                    if status_name == "DONE":
                        exit_code = 0

                return RunStatus(exit_code, status_name)

    def kill(self, process: ExecutedProcess):
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
        wait_result = self._executor.wait_for(self._executor.execute(wait_command))
        if wait_result.status.failed:
            raise ExecutorException(f"Waiting failed: {str(wait_result)}")
        return self.update_process(process).result
