# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
from abc import abstractmethod, ABCMeta
from builtins import property, bool, str
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from signal import Signals
from typing import Optional, TypeVar, Generic, ClassVar

from urllib3.util.url import Url

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.ExecutionState import ExecutionState, ObservedExecutionState
from weskit.classes.executor2.ProcessId import WESkitExecutionId, ProcessId, Identifier
from weskit.classes.storage.StorageAccessor import StorageAccessor
from weskit.memory_units import Memory
from weskit.serializer import decode_json

logger = logging.getLogger(__name__)


S = TypeVar("S")


class ExecutionResult(Generic[S]):
    """
    Any type of result information. Note that there can be intermediate results of a process,
    such as the currently produced standard output, even though the process is not terminated.
    Therefore, the exit_code is optional.

    Note that the process_id may be None, namely shortly after the process was submitted.
    """

    def __init__(self,
                 command: ShellCommand,
                 stdout_url: Optional[Url],
                 stderr_url: Optional[Url],
                 stdin_url: Optional[Url],
                 state: ObservedExecutionState[S],
                 start_time: datetime,
                 end_time: Optional[datetime] = None):
        self._command = command
        self._state = state
        self._stdout_url = stdout_url
        self._stderr_url = stderr_url
        self._stdin_url = stdin_url
        self._start_time = start_time
        self._end_time = end_time

    @property
    def execution_id(self) -> WESkitExecutionId:
        return self._state.execution_id

    @property
    def command(self) -> ShellCommand:
        return self._command

    @property
    def process_id(self) -> ProcessId:
        return self._state.last_external_state.pid

    @property
    def stdout_url(self) -> Optional[Url]:
        return self._stdout_url

    @property
    def stderr_url(self) -> Optional[Url]:
        return self._stderr_url

    @property
    def stdin_url(self) -> Optional[Url]:
        return self._stdin_url

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def state(self) -> ObservedExecutionState[S]:
        return self._state

    @state.setter
    def state(self, value: ObservedExecutionState[S]):
        self._state = value

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @end_time.setter
    def end_time(self, value: Optional[datetime]):
        self._end_time = value

    def __repr__(self):
        return "CommandResult(" + ", ".join([
            f"execution_id={self.execution_id}",
            f"command={self.command}",
            f"process_id={self.process_id}",
            f"status={self.state}"
        ]) + ")"


@dataclass
class ExecutionSettings:
    """
    Settings needed for executing the command on the execution infrastructure.
    All information is optional, and it is the responsibility of the Executor to decide, which of
    the information to use, or what to do if information is missing.
    """
    job_name: Optional[str] = None
    accounting_name: Optional[str] = None
    group: Optional[str] = None
    walltime: Optional[timedelta] = None
    memory: Optional[Memory] = None
    queue: Optional[str] = None
    # Fractional cores are relevant for Kubernetes.
    cores: Optional[float] = None
    # Whether the process can be restarted, and how often.
    max_retries: Optional[int] = None
    # The name of the container image, in which to execute the process.
    container_image: Optional[str] = None

    def __post_init__(self):
        """
        Some sanity checks on the values done at construction time of the dataclass instance.
        """
        if self.max_retries is not None:
            if self.max_retries < 0:
                raise ValueError("max_tries needs to be 0 or larger")
        if self.cores is not None:
            if self.cores <= 0:
                raise ValueError("walltime cores needs to be 1 or larger")
        if self.walltime is not None:
            if self.walltime.total_seconds() <= 0:
                raise ValueError("walltime total_seconds needs to be 1 or larger")
        if self.memory is not None:
            if self.memory.bytes() <= 0:
                raise ValueError("memory needs to be larger than 1 byte")

    def __iter__(self):
        for i in {
            "job_name": self.job_name,
            "accounting_name": self.accounting_name,
            "group": self.group,
            "walltime": self.walltime,
            "memory": self.memory,
            "queue": self.queue,
            "cores": self.cores,
            "max_retries": self.max_retries,
            "container_image": self.container_image,
        }.items():
            yield i

    def encode_json(self):
        # Note that because of the registered encoders, the typed fields (Memory, timedelta) will
        # be serialized by these. Here we return just the shallow encoding.
        return dict(self)

    @staticmethod
    def decode_json(args) -> ExecutionSettings:
        args["walltime"] = decode_json(args["walltime"])
        args["memory"] = decode_json(args["memory"])
        return ExecutionSettings(**args)

    @staticmethod
    def from_json(json_string: str) -> ExecutionSettings:
        return ExecutionSettings.decode_json(json.loads(json_string))


class Executor(Generic[S], metaclass=ABCMeta):
    """
    Execute a command on some execution infrastructure. Note that all operations may be blocking.
    All methods may throw an ProcessingError, if the command could not successfully be executed
    on the infrastructure. All other errors, such as parse errors, that occur because the output
    of a successfully executed command is unexpected are returned as ExecutorErrors.
    """

    EXECUTION_ID_VARIABLE: ClassVar[str] = "weskit_execution_id"

    def __init__(self,
                 id: Identifier[str],
                 log_dir_base: Optional[Path] = None):
        self._executor_id = id
        logger.info(f"Starting executor with ID {self._executor_id}")
        self._log_dir_base = log_dir_base if log_dir_base is not None else Path(".weskit")

    @property
    def log_dir_base(self) -> Path:
        return self._log_dir_base

    @property
    def id(self) -> Identifier[str]:
        """
        Executors are identifiable. The ID is reported in the logs.
        """
        return self._executor_id

    @property
    @abstractmethod
    def hostname(self) -> str:
        pass

    @abstractmethod
    async def execute(self,
                      execution_id: WESkitExecutionId,
                      command: ShellCommand,
                      stdout_file: Optional[Url] = None,
                      stderr_file: Optional[Url] = None,
                      stdin_file: Optional[Url] = None,
                      settings: Optional[ExecutionSettings] = None,
                      **kwargs) \
            -> ExecutionState[S]:
        """
        Submit a command to the execution infrastructure.

        The execution settings and the command are translated by the Executor into a (job)
        submission command (or REST call) that is then executed for the submission.

        The returned values is an ExecutorState with the WESkitProcessId you provided via the
        parameter.

        :param command: The command to be executed.
        :param execution_id: A WESkitExecutionId useful for re-identification of jobs, in case of
                    an interruption of the executor before the metadata have been stored.
        :param stdout_file: A URL to a file into which the standard output shall be written.
        :param stderr_file: A URL to a file into which the standard error shall be written.
        :param stdin_file: A URL to a file from which to take the process standard input.
        :param settings: Execution parameters on the execution infrastructure.
        :return: the ExecutorState[S] after submission

        Note that the stdout, stderr, and stdin files are always paths on the host that executes
        the process. Use the `Executor.storage` StorageAccessor to access the files.

        The submission of the process may fail, e.g., because

        * resources are not available, including the working dir is not accessible or the
          executable does not exist.
        * no external process ID could be retrieved.
        * no process could be created for any other reason.


        """
        pass

    @abstractmethod
    async def get_status(self,
                         execution_id: WESkitExecutionId,
                         log_dir: Optional[Url] = None,
                         pid: Optional[int] = None) \
            -> Optional[ExecutionState[S]]:
        """
        Get the status of the process in the execution infrastructure.

        If the state could not be retrieved, return None.
        """
        pass

    @abstractmethod
    async def update_status(self,
                            current_state: ExecutionState[S],
                            log_dir: Optional[Url] = None,
                            pid: Optional[int] = None)\
            -> Optional[ExecutionState[S]]:
        """
        Update the status of the executed process, if possible.

        If the state update fails, return None.
        """
        pass

    @abstractmethod
    async def get_result(self, state: ExecutionState[S]) \
            -> ExecutionResult[S]:
        """
        Query the executing backend for the status of the process and return the execution info.
        """
        pass

    @abstractmethod
    async def kill(self,
                   state: ExecutionState[S],
                   signal: Signals) \
            -> bool:
        """
        Cancel the process. Note that the killing operation may fail.
        Furthermore, note that if the process cannot be killed because it does not exist (anymore)
        no exception is thrown. Instead, if the process could not be found, False is returned.
        This is to reduce unnecessary exceptions in the common case where a process ends between
        the last status check and the killing command. Finally, even though the killing itself
        may not be immediately effective, this method immediately returns after sending the kill
        signal. You should call `wait_for` or poll the state yourself.
        """
        pass

    @abstractmethod
    async def wait(self, state: ExecutionState[S]) -> None:
        """
        Wait for the process to finish. This should be implemented efficiently, e.g. with wait
        (UNIX) or bwait (LSF). Avoid polling.

        Note that wait() is still async. The reasons are (1) the waiting may require calling an
        async method (e.g. a remote call), which would be hard without event loop, and (2) there
        is no reason to assume that the calling process should be blocked completely. Probably it
        will even get blocked async, because anyway also the other async methods of this class
        will be used in the same context.
        """
        pass

    @property
    @abstractmethod
    def storage(self) -> StorageAccessor:
        """
        Return a storage accessor for doing file operations on a (possibly remote) storage that is
        associated with the Executor. For instance, this may be an accessor for accessing storage
        via SSH, via NFS, or S3.
        """
        pass
