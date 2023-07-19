# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
from os import PathLike
from signal import Signals
from typing import Optional, Match

from classes.executor.ExecutionState import ExecutionState
from weskit.classes.executor.cluster.lsf.LsfState import LsfState
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import \
    Executor, ExecutionResult, ProcessId, ExecutionSettings
from weskit.classes.executor.ExecutorError import ExecutorError
from weskit.classes.executor.cluster.ClusterExecutor import ClusterExecutor, execute, CommandSet
from weskit.classes.executor.cluster.lsf.LsfCommandSet import LsfCommandSet
from weskit.utils import now

logger = logging.getLogger(__name__)


class LsfExecutor(ClusterExecutor[LsfState]):
    """
    Execute LSF job-management operations via shell commands issued on a local/remote host.
    """

    def __init__(self, executor: Executor):
        """
        Provide an executor that is used to execute the cluster commands. E.g. if this the commands
        should run locally, you can use a command_executor.LocalExecutor. If you need to submit via
        a remote connection, you can use a command_executor.SshExecutor.
        """
        super().__init__(executor)
        self.__command_set = LsfCommandSet()

    @property
    def _command_set(self) -> CommandSet:
        return self.__command_set

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def _jid_in_submission_output_pattern(self) -> str:
        return r'Job <(\d+)> is submitted to .+.\n'

    @property
    def _get_status_output_pattern(self) -> str:
        return r'(\d+)\s+(\S+)\s+(-|\d+)'

    def _extract_jid(self, match: Match[str]) -> str:
        return match.group(1)

    def _extract_status_name(self, match: Match[str]) -> str:
        return match.group(2)

    def _extract_exit_code(self, match: Match[str]) -> str:
        return match.group(3)

    @property
    def _success_status_name(self) -> str:
        return "DONE"

    @property
    def _success_exit_value(self) -> str:
        return "-"

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) -> ExecutionState[LsfState]:
        """
        WARNING: Do not set too many environment variables in `command.environment`. The
                implementation uses `bsub -env` and too many variables may result in a too long
                command-line.
        """

        if stdin_file is not None:
            logger.error("stdin_file is not supported in ClusterExecutor.execute()")
        # Note that there are at two shells involved: The environment on the submission host
        # and the environment on the compute-node, on which the actual command is executed.
        submission_command = self._command_set.submit(command=command,
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      settings=settings)
        # The actual submission is done quickly. We wait here for the
        # result and then use the cluster job ID returned from the submission command
        # as process ID to query the cluster's job status later.

        with execute(self._executor, submission_command) \
             as (result, stdout, stderr):
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()
            start_time = now()
            if result.status.failed:
                raise ExecutorError(f"Failed to submit cluster job: {result}, " +
                                    f"status={result.status}, " +
                                    f"stdout={stdout_lines}, " +
                                    f"stderr={stderr_lines}")
            else:
                cluster_job_id = \
                    ProcessId(self.extract_jobid_from_submission_output(stdout_lines))

        logger.debug(f"Cluster job ID {cluster_job_id}: {submission_command}")

        # NOTE: We could now create an additional `wait` process that waits for the cluster job
        # ID. However, we postpone the creation of this to a later stage.
        # The process handle is just the cluster job ID.
        return ExecutedProcess(executor=self,
                               process_handle=cluster_job_id,
                               pre_result=ExecutionResult(command=command,
                                                          process_id=cluster_job_id,
                                                          stderr_url=stderr_file,
                                                          stdout_url=stdout_file,
                                                          stdin_url=stdin_file,
                                                          status=ExecutionStatus(None),
                                                          start_time=start_time))

    def kill(self, state: ExecutionState[LsfState], signal: Signals = Signals.SIGINT) -> bool:
        raise NotImplementedError("should use bkill")
