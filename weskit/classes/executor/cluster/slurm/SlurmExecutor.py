# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import logging
import tempfile
from os import PathLike
from pathlib import Path

from typing import Optional, Match

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import \
    Executor, CommandResult, ProcessId, ExecutionSettings, ExecutedProcess, ExecutionStatus
from weskit.classes.executor.ExecutorError import ExecutorError
from weskit.classes.executor.cluster.ClusterExecutor import ClusterExecutor, execute, CommandSet
from weskit.classes.executor.cluster.slurm.SlurmCommandSet import SlurmCommandSet
from weskit.utils import now

logger = logging.getLogger(__name__)


class SlurmExecutor(ClusterExecutor):
    """
    Execute Slurm job-management operations via shell commands issued on a local/remote host.
    """

    def __init__(self, executor: Executor):
        """
        Provide an executor that is used to execute the cluster commands. E.g. if this the commands
        should run locally, you can use a command_executor.LocalExecutor. If you need to submit via
        a remote connection you can use an command_executor.SshExecutor.
        """
        super().__init__(executor)
        self.__command_set = SlurmCommandSet()
        self._shell_interpreter = '/bin/bash'

    @property
    def _command_set(self) -> CommandSet:
        return self.__command_set

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def _success_status_name(self) -> str:
        return "COMPLETED"

    @property
    def _jid_in_submission_output_pattern(self) -> str:
        return r'Submitted batch job (\d+)'

    @property
    def _success_exit_value(self) -> str:
        return "0"

    @property
    def _get_status_output_pattern(self) -> str:
        return r'(\d+)\s+(\S+)\s+(\d+):\d+'

    def _extract_jid(self, match: Match[str]) -> str:
        return match.group(1)

    def _extract_status_name(self, match: Match[str]) -> str:
        return match.group(2)

    def _extract_exit_code(self, match: Match[str]) -> str:
        return match.group(3)

    def _create_command_script(self, command: ShellCommand) -> Path:
        """
        We assume Bash is used on the remote side. The command (bash script) is written locally
        into a NamedTemporaryFile.
        """
        sub_command = command.command_expression
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
            if sub_command is not None:
                for export in ["#!" + self._shell_interpreter, sub_command]:
                    print(export, end="\n", sep=" ", file=file)
            return Path(file.name)

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) -> ExecutedProcess:
        """
        stdout, stderr, and stdin files are *remote files on the cluster nodes*.

        WARNING: Do not set too many environment variables in `command.environment`. The
                implementation uses `srun --export` and too many variables may result in a too long
                command-line.
        """

        if stdin_file is not None:
            logger.error("stdin_file is not supported in ClusterExecutor.execute()")
        # Note that there are at two shell involved: The environment on the submission host
        # and the environment on the compute-node, on which the actual command is executed.

        def _create_process(job_id: ProcessId,
                            execution_status: ExecutionStatus):
            process = ExecutedProcess(executor=self,
                                      process_handle=job_id,
                                      pre_result=CommandResult(command=command,
                                                               process_id=job_id,
                                                               stderr_file=stderr_file,
                                                               stdout_file=stdout_file,
                                                               stdin_file=stdin_file,
                                                               start_time=now(),
                                                               execution_status=execution_status))
            return process

        source_script = self._create_command_script(command)
        target_script = Path(str(command.workdir), ".weskit_submitted_command.sh")
        try:
            self._event_loop.run_until_complete(self.storage.put(source_script, target_script))
        except ExecutorError:
            return _create_process(job_id=ProcessId(0),
                                   execution_status=ExecutionStatus(1, "EXIT"))

        # Note that source and target are never the same file. Thus, the latter removal will only
        # remove the (possibly remote) copy.

        command.command = [str(target_script)]
        submission_command = self._command_set.submit(command=command,
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      settings=settings)
        # The actual submission is done quickly. We wait here for the
        # result and then use the cluster job ID returned from the submission command, as process
        # ID to query the cluster job status later.

        with execute(self._executor, submission_command) \
             as (result, stdout, stderr):
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()
            if result.status.failed:
                raise ExecutorError(f"Failed to submit cluster job: {result}, " +
                                    f"stdout={stdout_lines}, " +
                                    f"stderr={stderr_lines}")
            else:
                cluster_job_id = \
                    ProcessId(self.extract_jobid_from_submission_output(stdout_lines))

        # Remove the remote file once the submission has been executed.
        self._event_loop.run_until_complete(self.storage.remove_file(target_script))

        logger.debug(f"Cluster job ID {cluster_job_id}: {submission_command}")
        # NOTE: We could now create an additional `wait` process that waits for the cluster job
        # ID. However, we postpone the creation of this to a later stage. The process
        # handle is just the cluster job ID.
        return _create_process(job_id=cluster_job_id,
                               execution_status=ExecutionStatus(None))

    def kill(self, process: ExecutedProcess):
        raise NotImplementedError()
