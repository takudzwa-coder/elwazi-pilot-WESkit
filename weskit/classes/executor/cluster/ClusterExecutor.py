#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import re
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, List, Tuple, Iterator, IO, Match, cast

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import \
    Executor, ExecutedProcess, ExecutionStatus, CommandResult, ExecutionSettings, FileRepr
from weskit.classes.executor.ExecutorException import \
    ExecutorException, ExecutionError, TimingError
from weskit.utils import now

logger = logging.getLogger(__name__)


@contextmanager
def execute(executor: Executor,
            command: ShellCommand,
            encoding: Optional[str] = "utf-8",
            **kwargs) \
        -> Iterator[Tuple[CommandResult, IO[str], IO[str]]]:
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
                                    stdout_file=Path(stdout.name),
                                    stderr_file=Path(stderr.name),
                                    **kwargs)
            result = executor.wait_for(proc)
            yield result, stdout, stderr


class CommandSet(metaclass=ABCMeta):

    @abstractmethod
    def submit(self,
               command: ShellCommand,
               stdout_file: Optional[PathLike] = None,
               stderr_file: Optional[PathLike] = None,
               # stdin_file: Optional[PathLike] = None,  # possible with `-i`, but not needed
               settings: Optional[ExecutionSettings] = None) -> ShellCommand:
        pass

    @abstractmethod
    def get_status(self, job_ids: List[str]) -> ShellCommand:
        """
        Get a command that lists the job states for the requested jobs.
        """
        pass

    @abstractmethod
    def kill(self, job_ids: List[str], signal: str = "TERM") -> ShellCommand:
        """
        Get the command to send a termination signal to the jobs.
        """
        pass

    @abstractmethod
    def wait_for(self, job_id: str) -> ShellCommand:
        """
        A command that blocks (up to a year), until the requested job ended.
        """
        pass


def is_retryable_error(exception: BaseException) -> bool:
    return isinstance(exception, (ExecutionError, TimingError))


class ClusterExecutor(Executor):
    """
    Execute job-management operations via shell commands issued on a local/remote host.
    """
    @abstractmethod
    def __init__(self,
                 executor: Executor):
        """
        Provide an executor that is used to execute the cluster specific commands.
        E.g. if this the commands should run locally, you can use a command_executor.LocalExecutor.
        If you need to submit via a remote connection, you can use a command_executor.SshExecutor.
        """
        self._executor = executor

    def copy_file(self, source: Path, target: Path):
        self._executor.copy_file(source, target)

    def remove_file(self, target: Path):
        self._executor.remove_file(target)

    @property
    @abstractmethod
    def _command_set(self) -> CommandSet:
        pass

    @property
    @abstractmethod
    def _jid_in_submission_output_pattern(self) -> str:
        pass

    def extract_jobid_from_submission_output(self, output: List[str]):
        if len(output) == 0:
            raise ExecutorException("No parsable output during job submission")
        # Sometimes job submission may be delayed, because the cluster is overloaded.
        # I this situation a number of diagnostic messages are shown, but eventually, the
        # submission line is displayed. We simply try to parse all these lines and are happy
        # with the first line that matches.
        matches = map(lambda l: re.match(self._jid_in_submission_output_pattern, l), output)
        first_match = next(filter(lambda m: bool(m), matches), None)
        if first_match is None:
            raise ExecutorException(f"Could not parse job ID from: {output}")
        return first_match.group(1)

    @property
    @abstractmethod
    def _success_status_name(self) -> str:
        pass

    @property
    @abstractmethod
    def _success_exit_value(self) -> str:
        """
        This is not necessarily a number.
        """
        pass

    @property
    @abstractmethod
    def _get_status_output_pattern(self) -> str:
        """
        A pattern that is matched on the output lines of the status query command of the cluster.
        The following _extract_* methods are used to extract specific information from the match
        result of this pattern.
        """
        pass

    @abstractmethod
    def _extract_jid(self, match: Match[str]) -> str:
        pass

    @abstractmethod
    def _extract_status_name(self, match: Match[str]) -> str:
        pass

    @abstractmethod
    def _extract_exit_code(self, match: Match[str]) -> str:
        pass

    def parse_get_status_output(self,
                                stdout_lines: List[str]) \
            -> Tuple[str, str, str]:
        """
        Throws a ValueError, if not exactly a single stdout_line matches the status output pattern.

        :param stdout_lines:
        :return: job_id, status_name, exit_code
        """
        # Jobs may produce multiple lines output, if it has to wait for the
        # job submission server to answer. We assume that we are only interested
        # in those lines matching the regular expression.
        match_lines: List[Match[str]] = \
            list(map(lambda m: cast(Match[str], m),   # get rid of the optional type for mypy
                     filter(lambda m: bool(m),
                            map(lambda line: re.match(self._get_status_output_pattern,
                                                      line.rstrip()),
                                stdout_lines))))
        if len(match_lines) != 1:
            raise ValueError(len(match_lines))

        # Now get the information about the job executed on the cluster.
        job_id, status_name, reported_exit_code = \
            self._extract_jid(match_lines[0]), \
            self._extract_status_name(match_lines[0]), \
            self._extract_exit_code(match_lines[0])

        return job_id, status_name, reported_exit_code

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6),
           stop=stop_after_attempt(4),
           retry=retry_if_exception(is_retryable_error))
    def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
        status_command = self._command_set.get_status([process.id.value])
        with execute(self._executor, status_command) as (result, stdout, stderr):
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()
            base_error_info = ", ".join([
                f"command={status_command}",
                f"result={result}",
                f"stdout={stdout_lines}"
                f"stderr={stderr_lines}"
                ])
            if not result.status.success:
                raise ExecutionError("Could not request status. " + base_error_info)
            if len(stdout_lines) == 0:
                # In case command was successfully executed but output is
                # 'blocked' by the server (slurm).
                raise TimingError("Status is empty. " + base_error_info)
            try:
                job_id, status_name, reported_exit_code = \
                    self.parse_get_status_output(stdout_lines)
            except ValueError:
                raise ExecutorException("No unique match of status. " + base_error_info)

            if job_id != str(process.id.value):
                raise ExecutorException("Job ID didn't match the parsed one. " + base_error_info)

            # The reported exit code is '-' if the job is still running, or if the job
            # is done with return value 0.
            exit_code: Optional[int]
            if reported_exit_code == self._success_exit_value:
                if status_name == self._success_status_name:
                    exit_code = 0
                else:
                    exit_code = None
            else:
                exit_code = int(reported_exit_code)

            return ExecutionStatus(exit_code, status_name)

    def kill(self, process: ExecutedProcess):
        # Not tested therefore
        raise NotImplementedError("kill on ClusterExecutor is not tested")
        # kill_command = ShellCommand(self._command_set.kill(process.id.value))
        # self._executor.wait_for(self._executor.execute(kill_command))

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        old_status = process.result.status
        process.result.status = self.get_status(process)
        if old_status.code is None:
            # The status is changed. We avoid having to parse the finishing time of the job (we
            # could use `bjobs -o "finish_time"), because it is complex and configurable. See
            # e.g. the code in BatchEuphoria (https://tinyurl.com/27x44ndb). The following is the
            # cheap solution and sufficient for us, because we always call wait_for().
            process.result.end_time = now()
        return process

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        if process.result.status.finished:
            return process.result
        wait_command = self._command_set.wait_for(process.id.value)
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

    @abstractmethod
    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[FileRepr] = None,
                stderr_file: Optional[FileRepr] = None,
                stdin_file: Optional[FileRepr] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) \
            -> ExecutedProcess:
        """
        Submit a command to the execution infrastructure.

        The execution settings and the command are translated by the Executor into a (job)
        submission command (or REST call) that is then executed for the submission.

        The return value is a representation of the executed process.

        References to environment variables in the command-line will not be evaluated. If you want
        these variables to be evaluated, you need to wrap the command in a shell, e.g.

           command = ["bash", "-c", "echo $someVar"]

        :param command: The command to be executed.
        :param stdout_file: A path to a file into which the standard output shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.o%J
        :param stderr_file: A path to a file into which the standard error shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.e%J
        :param stdin_file: A path to a file from which to take the process standard input.
        :param settings: Execution parameters on the execution infrastructure.
        :return: A representation of the executed command.
        """
        pass
