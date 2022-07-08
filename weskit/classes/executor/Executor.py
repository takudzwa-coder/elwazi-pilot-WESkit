#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import abc
import json
from builtins import property, bool, str
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import PathLike
from pathlib import PurePath
from typing import Optional, Any, Union, IO

from weskit.serializer import decode_json
from weskit.classes.ShellCommand import ShellCommand
from weskit.memory_units import Memory


class ProcessId:
    """
    This is for the process ID on the executor. I.e. if the process is not run directly, but e.g.
    on a different compute node as a cluster job, then the ExecutorProcessId shall be the cluster
    job ID.
    """
    def __init__(self, value: Optional[Any]):
        self._value = value

    @property
    def value(self):
        return self._value

    def __repr__(self) -> str:
        return f"ProcessId({self.value})"


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


# Some executors support using streams, filedescriptors, etc. so more general file representations
# as parameters for stdout and stderr. We declare the type here.
FileRepr = Union[PathLike, IO[str]]


class CommandResult:
    """
    Any type of result information. Note that there can be intermediate results of a process,
    such as the currently produced standard output, even though the process is not terminated.
    Therefore, the exit_code is optional.
    """

    def __init__(self,
                 command: ShellCommand,
                 id: ProcessId,
                 stdout_file: Optional[FileRepr],
                 stderr_file: Optional[FileRepr],
                 stdin_file: Optional[FileRepr],
                 execution_status: ExecutionStatus,
                 start_time: datetime,
                 end_time: Optional[datetime] = None):
        self._command = command
        self._process_id = id
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
    def id(self) -> ProcessId:
        return self._process_id

    @property
    def stdout_file(self) -> Optional[FileRepr]:
        return self._stdout_file

    @property
    def stderr_file(self) -> Optional[FileRepr]:
        return self._stderr_file

    @property
    def stdin_file(self) -> Optional[FileRepr]:
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
        return f"CommandResult(command={self.command}, id={self.id}, status={self.status})"


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
    cores: Optional[int] = None

    def __iter__(self):
        for i in {
            "job_name": self.job_name,
            "accounting_name": self.accounting_name,
            "group": self.group,
            "walltime": self.walltime,
            "memory": self.memory,
            "queue": self.queue,
            "cores": self.cores
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
    """

    # Note: The Executor is a forward reference to a not yet declared class. Either use
    # `from __future__ import annotation` or make the forward reference a string by quoting,
    # i.e. 'Executor'.
    def __init__(self,
                 executor: Executor,
                 process_handle,
                 pre_result: CommandResult):
        self._executor = executor
        self._process_handle = process_handle
        self._result = pre_result

    @property
    def handle(self):
        """
        Only for access from Executor.
        """
        return self._process_handle

    @property
    def command(self) -> ShellCommand:
        return self._result.command

    @property
    def id(self) -> ProcessId:
        """
        Note that the process ID can be the one used by the underlying execution infrastructure,
        but could also be implemented in the subclass including some process management. It
        primarily serves to address the process in the Executor.
        """
        return self._result.id

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


class Executor(metaclass=abc.ABCMeta):
    """
    Execute a command on some execution infrastructure. Note that all operations may be blocking.
    All methods may throw an ExecutionError, if the command could not successfully be executed
    on the infrastructure. All other errors, such as parse errors, that occur because the output
    of a successfully executed command is unexpected are returned as ExecutorExceptions.
    """

    @abc.abstractmethod
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
        in a finished state, this function updates to the the intermediate results at the time of
        the query. The CommandResult may thus contain no exit code.
        """
        pass

    @abc.abstractmethod
    def kill(self, process: ExecutedProcess):
        """
        Cancel the the process named by the process_id. Note that the killing operation may fail.
        Furthermore, note that if the process cannot be killed because it does not exist (anymore)
        no exception is thrown. This is to reduce unnecessary exceptions in the common case where
        a process ends between the last status check and the killing command. The killing of a
        process may take time on some infrastructures or may take time to be send remotely.
        Consequently, this function may block.
        """
        pass

    @abc.abstractmethod
    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        """
        Wait for the executed process and return the CommandResult. The ExecutedProcess is updated
        with the most recent result object.
        """
        pass

    @abc.abstractmethod
    def copy_file(self, source: PurePath,  target: PurePath):
        """
        Copy a file associated with the execution of a job from source to target. If the target is
        remote then this corresponds to a network transfer.
        """
        pass

    @abc.abstractmethod
    def remove_file(self, target: PurePath):
        """
        Remove the target file. The target can be remote.
        """
        pass
