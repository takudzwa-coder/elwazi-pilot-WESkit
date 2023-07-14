# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import abc
import json
import logging
from asyncio import AbstractEventLoop
from builtins import property, bool, str
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import PathLike
from typing import Optional, TypeVar
from uuid import uuid4, UUID

import ulid
from ulid.api import ULID

from weskit.utils import get_event_loop
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.storage.StorageAccessor import StorageAccessor
from weskit.memory_units import Memory
from weskit.serializer import decode_json

logger = logging.getLogger(__name__)


class WESkitProcessId:
    """
    A process ID assigned by WESkit **before** the submission of a process to the executor.
    This ID can be used to implement recovery with

    1. Create WESkitProcessId wid
    2. Store wid in DB
    3. Submit process with wid as ID to executor that can be used for re-identification.
    4. Update DB with submission data
    """

    def __init__(self):
        self._value = ulid.new()

    @property
    def value(self) -> ULID:
        return self._value

    def __repr__(self) -> str:
        return f"WESkitProcessId(value={str(self.value)})"


T = TypeVar("T")


class ProcessId:
    """
    This is for the process ID on the executor. I.e. if the process is not run directly, but e.g.
    on a different compute node as a cluster job, then the ExecutorProcessId shall be the cluster
    job ID.

    The process ID's value is the native ID of the executor, such as a UNIX PID or a cluster job
    ID assigned by the cluster upon submission. It is available only **after** the submission.

    The process ID's tag is an internal identifier of the process that is just a unique string
    and can be used to retrieve the process ID value from the execution infrastructure, in the
    case that the submission succeeded, but the value couldn't be stored in the DB anymore, e.g.
    in case of network failure or died worker containers.

    Every process gets a process tag, whether you set it or not. The default is a UUID string.
    """
    def __init__(self,
                 value: Optional[T]):
        self._value = value

    @property
    def value(self) -> Optional[T]:
        return self._value

    def __repr__(self) -> str:
        return f"ProcessId(value={str(self.value)})"


class ExecutionStatus:
    """
    The ExecutionStatus is the status of the command execution on the execution infrastructure.
    Usually, this is just an integer, which is available, if the process is still running.
    In a cluster, there can also be a status name, e.g. PENDING or similar, as issued by the
    cluster system.
    """

    def __init__(self,
                 code: Optional[int] = None,
                 name: Optional[str] = None,
                 message: Optional[str] = None):
        """
        :param code: Exit code of the process, if available.
        :param name: A possible status name, e.g. PENDING or similar, according to the execution
                     infrastructure
        :param message: If available a message, such as an error message from the infrastructure.
        """
        self._code = code
        self._name = name
        self._message = message

    @property
    def code(self) -> Optional[int]:
        return self._code

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def message(self) -> Optional[str]:
        return self._message

    @property
    def finished(self) -> bool:
        """
        Return whether the process is in a finished state (successful or not).
        """
        return self.code is not None

    @property
    def success(self) -> bool:
        """
        Return whether the command is a success state.
        """
        return self.code is not None and self.code == 0

    @property
    def failed(self) -> bool:
        """
        Return whether the command is in failed state.
        """
        return self.code is not None and self.code != 0

    def __str__(self) -> str:
        return f"ExecutionStatus(code={self.code}" + \
               (f", name={self.name}" if self.name is not None else "") + \
               (f", message={self.message}" if self.message is not None else "") +\
               ")"


class CommandResult:
    """
    Any type of result information. Note that there can be intermediate results of a process,
    such as the currently produced standard output, even though the process is not terminated.
    Therefore, the exit_code is optional.

    Note that the process_id may be None, namely shortly after the process was submitted
    """

    def __init__(self,
                 command: ShellCommand,
                 process_id: ProcessId,
                 stdout_file: Optional[PathLike],
                 stderr_file: Optional[PathLike],
                 stdin_file: Optional[PathLike],
                 execution_status: ExecutionStatus,
                 start_time: datetime,
                 end_time: Optional[datetime] = None):
        self._command = command
        self._process_id = process_id
        self._execution_status = execution_status
        self._stdout_file = stdout_file
        self._stderr_file = stderr_file
        self._stdin_file = stdin_file
        self._start_time = start_time
        self._end_time = end_time

    @property
    def command(self) -> ShellCommand:
        return self._command

    @property
    def process_id(self) -> ProcessId:
        return self._process_id

    @process_id.setter
    def process_id(self, id: ProcessId) -> None:
        self.process_id = id

    @property
    def stdout_file(self) -> Optional[PathLike]:
        return self._stdout_file

    @property
    def stderr_file(self) -> Optional[PathLike]:
        return self._stderr_file

    @property
    def stdin_file(self) -> Optional[PathLike]:
        return self._stdin_file

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def status(self) -> ExecutionStatus:
        return self._execution_status

    @status.setter
    def status(self, value: ExecutionStatus):
        self._execution_status = value

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @end_time.setter
    def end_time(self, value: Optional[datetime]):
        self._end_time = value

    def __repr__(self):
        return f"CommandResult(command={self.command}, id={self.process_id}, status={self.status})"


@dataclass
class ExecutionSettings:
    """
    Any information that is needed for executing the command on the execution infrastructure.
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
    max_retries: Optional[int] = None
    container_image: Optional[str] = None

    def __post_init__(self):
        """
        Some sanity checks on the values done at construction time of the dataclass instance.
        """
        if self.max_retries is not None:
            assert(self.max_retries >= 0)
        if self.cores is not None:
            assert(self.cores > 0)
        if self.walltime is not None:
            assert(self.walltime.total_seconds() > 0)
        if self.memory is not None:
            assert(self.memory.bytes() > 0)

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


class ExecutedProcess(metaclass=abc.ABCMeta):
    """
    The command is submitted to the executor, which returns this as a handle for the executed
    process. ExecutedProcess delegates to the Executor it originated from, which saves
    us from having to implement some kind of process management, just in case we will have multiple
    processes in the same thread.

    ExecutedProcess is serializable and can be stored in the database, such that another process
    or thread can connect to the process running in the executor infrastructure.
    """

    # Note: The Executor is a forward reference to a not yet declared class. Either use
    # `from __future__ import annotation` or make the forward reference a string by quoting,
    # i.e. 'Executor'.
    def __init__(self,
                 executor: Executor,
                 weskit_id: WESkitProcessId,
                 pre_result: CommandResult):
        self._executor = executor
        self._wid = weskit_id
        self._result = pre_result

    @property
    def wid(self):
        """
        Only for access from Executor.
        """
        return self._wid

    @property
    def command(self) -> ShellCommand:
        return self._result.command

    @property
    def pid(self) -> ProcessId:
        """
        Note that the process ID can be the one used by the underlying execution infrastructure,
        but could also be implemented in the subclass including some process management. It
        primarily serves to address the process in the Executor.
        """
        return self._result.process_id

    def update_result(self) -> ExecutedProcess:
        """
        Update the result object and return the self (for method chaining).
        """
        self._executor.update_process(self)
        return self

    @property
    def result(self) -> CommandResult:
        """
        Return the cached result object. If you want to update do

            proc.update_result().result
        """
        return self._result

    @result.setter
    def result(self, value: CommandResult):
        self._result = value

    def detach(self) -> None:
        pass


class Executor(metaclass=abc.ABCMeta):
    """
    Execute a command on some execution infrastructure. Note that all operations may be blocking.
    All methods may throw an ProcessingError, if the command could not successfully be executed
    on the infrastructure. All other errors, such as parse errors, that occur because the output
    of a successfully executed command is unexpected are returned as ExecutorErrors.
    """

    def __init__(self,
                 event_loop: Optional[AbstractEventLoop] = None):
        """
        Some the methods are asynchronous. We keep an event loop ready for them.
        """
        self._executor_id = uuid4()
        logger.info(f"Starting executor with ID {self._executor_id}")
        if event_loop is None:
            self._event_loop = get_event_loop()
        else:
            self._event_loop = event_loop

    @property
    def id(self) -> UUID:
        return self._executor_id

    @property
    @abc.abstractmethod
    def hostname(self) -> str:
        """
        #!/bin/bash

        set -o pipefail -ue

        logPath="${1:?No log path given}"
        shift 1

        declare -a command=( $@ )

        # UNIX `false` cannot return arbitrary exit code, and `return` is not allowed in a {}
        # block, and `exit` does not return from the block but ends the whole shell.
        with_code() {
          local code="${1:-0}"
          return $code
        }

        # Run the command and collect all information
        {
          "$command[@]" &
          echo "$!" > "$logPath/pid"
          wait
          exit_code="$?"
          echo "$exit_code" > "$logPath/exit_code"
          with_code "$exit_code"
        } \
          1> >(tee stdout > "$logPath/stdout") \
          2> >(tee stderr > "$logPath/stderr")
          <($logPath/stdin)
        """
        pass

    # TODO Create a process directory
    # TODO Create a wrapper and write it via the storage accessor to the process directory.
    def _wrapper(self):
        pass

    @abc.abstractmethod
    def execute(self,
                command: ShellCommand,
                wid: Optional[WESkitProcessId] = None,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) \
            -> ExecutedProcess:
        """
        Submit a command to the execution infrastructure.

        The execution settings and the command are translated by the Executor into a (job)
        submission command (or REST call) that is then executed for the submission.

        The return value is a representation of the executed process.

        :param command: The command to be executed.
        :param wid: An optional WESkitProcessId useful for re-identification of jobs, in case of
                    an interruption of the executor before the metadata have been stored.
        :param stdout_file: A path to a file into which the standard output shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.o%J
        :param stderr_file: A path to a file into which the standard error shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.e%J
        :param stdin_file: A path to a file from which to take the process standard input.
        :param settings: Execution parameters on the execution infrastructure.
        :return: A representation of the executed command.

        Note that the stdout, stderr, and stdin files are always paths on the host that executes
        the process. Use the `Executor.storage` StorageAccessor to access the files.
        """
        pass

    # It is not the responsibility of the ExecutedProcess to know how to query its status or
    # how to get killed by the executor, etc. Therefore, the ExecutedProcess is handed back to the
    # Executor for the following operations.

    @abc.abstractmethod
    def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
        """
        Get the status of the process in the execution infrastructure. The `process.result` is not
        modified.
        """
        pass

    @abc.abstractmethod
    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        """
        Update the result of the executed process, if possible. If the status of the process is not
        in a finished state, this function updates to the intermediate results at the time of
        the query. The CommandResult may thus contain no exit code.
        """
        pass

    @abc.abstractmethod
    def kill(self, process: ExecutedProcess) -> bool:
        """
        Cancel the process. Note that the killing operation may fail.
        Furthermore, note that if the process cannot be killed because it does not exist (anymore)
        no exception is thrown. Instead, if the process could not be found, False is returned.
        This is to reduce unnecessary exceptions in the common case where a process ends between
        the last status check and the killing command. Finally, even though the killing itself
        may not be immediately effective, this method immediately returns after sending the kill
        signal.
        """
        pass

    @abc.abstractmethod
    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        """
        Wait for the executed process and return the CommandResult. The ExecutedProcess is updated
        with the most recent result object.
        """
        pass

    @property
    @abc.abstractmethod
    def storage(self) -> StorageAccessor:
        """
        Return a storage accessor for doing file operations on a (possibly remote) storage that is
        associated with the Executor. For instance, this may be an accessor for accessing storage
        via SSH, via NFS, or S3.
        """
        pass
