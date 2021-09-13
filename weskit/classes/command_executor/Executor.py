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
from builtins import property, bool, str
from os import PathLike
from typing import Optional

from weskit.classes.ShellCommand import ShellCommand


class ValueClass(metaclass=abc.ABCMeta):
    """
    Multiple classes have a value property, but should be distinct types.
    """

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value


class ExecutorProcessId(ValueClass, metaclass=abc.ABCMeta):
    """
    This is for the process ID on the executor. I.e. if the process is not run directly, but e.g.
    on a different compute node as a cluster job, then the ExecutorProcessId shall be the cluster
    job ID.
    """
    pass


class RunStatus(ValueClass, metaclass=abc.ABCMeta):
    """
    The RunStatus is the status of the command execution on the execution infrastructure, e.g.
    the job status in the cluster.
    """

    @property
    @abc.abstractmethod
    def finished(self) -> bool:
        """
        Return whether the process is in a finished state (successful or not).
        """
        pass

    @property
    @abc.abstractmethod
    def success(self) -> bool:
        """
        Return whether the command is an success state.
        """
        pass

    @property
    @abc.abstractmethod
    def failed(self) -> bool:
        """
        Return whether the command is in failed state.
        """
        pass


class CommandResult:
    """
    Any type of result information. Note that there can be intermediate results of a process,
    such as the currently produced standard output, even though the process is not terminated.
    Therefore, the exit_code is optional.
    """

    def __init__(self,
                 id: ExecutorProcessId,
                 stdout_file: PathLike,
                 stderr_file: PathLike,
                 run_status: RunStatus,
                 start_time: str,
                 end_time: Optional[str] = None):
        self._process_id = id
        self._run_status = run_status
        self._stdout_file = stdout_file
        self._stderr_file = stderr_file
        self._start_time = start_time
        self._end_time = end_time

    @property
    def id(self) -> ExecutorProcessId:
        return self._process_id

    @property
    def stdout_file(self) -> PathLike:
        return self._stdout_file

    @property
    def stderr_file(self) -> PathLike:
        return self._stderr_file

    @property
    def start_time(self) -> str:
        return self._start_time

    @property
    def status(self) -> RunStatus:
        return self._run_status

    @status.setter
    def status(self, value: RunStatus):
        self._run_status = value

    @property
    def end_time(self) -> Optional[str]:
        return self._end_time

    @end_time.setter
    def end_time(self, value: str):
        self._end_time = value


class ExecutionSettings(metaclass=abc.ABCMeta):
    """
    Any information that is needed for executing the command on the execution infrastructure.
    Examples are hard/soft memory requirements, CPU usage, and walltime.
    """
    pass


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
                 command: ShellCommand,
                 executor: Executor,
                 process_handle,
                 pre_result: CommandResult):
        self._command = command
        self._executor = executor
        self._process_handle = process_handle
        self._result = pre_result

    @property
    def command(self) -> ShellCommand:
        return self._command

    @property
    def handle(self):
        return self._process_handle

    @property
    @abc.abstractmethod
    def process_id(self) -> ExecutorProcessId:
        """
        Note that the process ID can be the one used by the underlying execution infrastructure,
        but could also be implemented in the subclass including some process management. It
        primarily serves to address the process in the Executor.
        """
        pass

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
    All methods may throw an ExecutorException, if the command could not successfully be executed
    on the infrastructure.
    """

    @abc.abstractmethod
    def submit(self,
               command: ShellCommand,
               stdout_file: PathLike,
               stderr_file: PathLike,
               settings: Optional[ExecutionSettings] = None) \
            -> ExecutedProcess:
        """
        Submit a command to the execution infrastructure.

        The execution settings and the command are translated by the Executor into a (job)
        submission command (or REST call) that is then executed for the submission.

        The return value is a representation of the executed process.

        :param command: The command to be executed.
        :param stdout_file: A path to a file into which the standard output shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.o%J
        :param stderr_file: A path to a file into which the standard error shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.e%J
        :param settings: Execution parameters on the execution infrastructure.
        :return: A representation of the executed command.
        """
        pass

    # It is not the responsibility of the ExecutedProcess to know how to query its status or
    # how to get killed by the executor, etc. Therefore, the ExecutedProcess is handed back to the
    # Executor for the following operations.

    @abc.abstractmethod
    def get_status(self, process: ExecutedProcess) -> RunStatus:
        """
        Get the status of the process in the execution infrastructure.
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
    def kill(self, process: ExecutedProcess) -> bool:
        """
        Cancel the the process named by the process_id. Note that the killing operation may fail.
        Furthermore, note that if the process cannot be killed because it does not exist (anymore)
        no exception is thrown. This is to reduce unnecessary exceptions in the common case where
        a process ends between the last status check and the killing command. Returns true if the
        process is not running after the killing command, otherwise false. The killing of a process
        may take time on some infrastructures. Consequently, this function may block.
        """
        pass

    @abc.abstractmethod
    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        """
        Wait for the executed process and return the CommandResult. The ExecutedProcess is updated
        with the most recent result object.
        """
        pass
