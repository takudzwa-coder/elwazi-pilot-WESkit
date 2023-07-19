#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import glob
import logging
import os
import re
import socket
import subprocess  # nosec B603 B404
from abc import ABCMeta, abstractmethod
from asyncio import AbstractEventLoop
from builtins import super, property
from importlib.abc import Traversable
from pathlib import Path
from signal import Signals
from typing import Optional, List, TypeVar, Generic, cast

from urllib3.util.url import Url

from classes.storage.StorageAccessor import StorageAccessor
from utils import resource_path
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.ExecutionState import ExecutionState, ExternalState, Failed, Start
from weskit.classes.executor.Executor import Executor, ExecutionSettings
from weskit.classes.executor.ExecutorError import NonRetryableExecutorError
from weskit.classes.executor.ProcessId import WESkitExecutionId, ProcessId
from weskit.classes.executor.unix.UnixStates import UnixState, UnixStateMapper
from weskit.classes.storage.LocalStorageAccessor import LocalStorageAccessor

logger = logging.getLogger(__name__)


S = TypeVar("S")


class UnixExecutor(Generic[S], Executor[S], metaclass=ABCMeta):
    """
    Execute commands in a Unix process. The commands are executed asynchronously in the background
    managed by the operating system.
    """

    _map_to_next_state = UnixStateMapper()

    def __init__(self,
                 storage: StorageAccessor,
                 event_loop: Optional[AbstractEventLoop] = None):
        super().__init__(event_loop)
        self._storage = storage

    @property
    def storage(self) -> StorageAccessor:
        return self._storage

    @property
    @abstractmethod
    def hostname(self) -> str:
        """
        A hostname identifying the system/container on which the process runs.
        """
        pass

    def _log_dir(self,
                 workdir: Optional[Path],
                 execution_id: WESkitExecutionId) -> Path:
        if workdir is not None:
            return workdir / f".weskit-{execution_id.value}"
        else:
            return Path(f".weskit-{execution_id.value}")

    def _file_url_to_path(self, url: Url) -> Path:
        if url.scheme is not None and url.scheme is not "file":
            raise ValueError("LocalExecutor only accepts file:// URLs for stdin/stdout/stderr")
        else:
            return Path(url.path)

    @property
    def _wrapper_source_path(self) -> Path:
        return cast(Path, resource_path("weskit.classes.executor.resources", "wrap"))

    @abstractmethod
    def _wrapper_path(self, stage_path: Optional[Path] = None) -> Path:
        pass

    def _wrapped_command(self,
                         execution_id: WESkitExecutionId,
                         command: ShellCommand,
                         stdout_url: Optional[Url] = None,
                         stderr_url: Optional[Url] = None,
                         stdin_url: Optional[Url] = None
                         )\
            -> ShellCommand:
        """
        Return a ShellCommand derived from the input command that allows the command to be run
        in the background and includes logging to the requested output files and of the
        exit code.

        The execution logs go into a directory `.log-{execution_id}`, unless other files
        were requested via the `stdout_url`, etc. parameters.
        """
        def _optional_file(param: str, url: Optional[Url]) -> List[str]:
            if url is not None:
                path = self._file_url_to_path(url)
                return [param, path]
        log_dir = self._log_dir(command.workdir, execution_id)
        wrapped_command = [self._wrapper_path(log_dir), "-a"]
        wrapped_command += ["-l", log_dir]
        wrapped_command += _optional_file("-o", stdout_url)
        wrapped_command += _optional_file("-e", stderr_url)
        wrapped_command += _optional_file("-i", stdin_url)
        wrapped_command += ["--", command.command_expression]
        return command.copy(command=wrapped_command)

    def execute(self,
                execution_id: WESkitExecutionId,
                command: ShellCommand,
                stdout_url: Optional[Url] = None,
                stderr_url: Optional[Url] = None,
                stdin_url: Optional[Url] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) \
            -> ExecutionState[UnixState]:
        effective_command = self._wrapped_command(execution_id,
                                                  command,
                                                  stdout_url,
                                                  stderr_url,
                                                  stdin_url)
        execution_state = Start(execution_id)
        log_dir = self._log_dir(command.workdir, execution_id)
        try:
            # Note: If the log dir exists this means that the execution_id was reused. The
            #       execution_id, however should be used for a single execution attempt only!
            log_dir.mkdir(parents=True, exist_ok=False, mode=0o750)

            process = subprocess.Popen(effective_command.command,
                                       cwd=command.workdir,
                                       env={
                                           # Tag the process with `weskit_process_id` to make it
                                           # recoverable with a query of the environment variables
                                           # of process (e.g. on /proc/).
                                           Executor.EXECUTION_ID_VARIABLE: str(execution_id),
                                           **command.environment
                                       },
                                       shell=False,
                                       # Run the process in the background and detached from Python.
                                       close_fds=True,
                                       **kwargs)

            # The process already was sent to the background. We recover the process information.
            execution_state = self.update_status(execution_state,
                                                 Url(scheme="file",
                                                     path=str(log_dir)),
                                                 process.pid)
            logger.debug(f"Started process {execution_id} with PID " +
                         f"{process.pid}: {effective_command}")
            return execution_state

        except FileNotFoundError as e:
            # The other executors recognize inaccessible working directories or missing commands
            # only after the wait_for(). We emulate this behaviour here such that all executors
            # behave identically with respect to these problems.
            if str(e).startswith(f"[Errno 2] No such file or directory: {repr(command.workdir)}"):
                # cd /dir/does/not/exist: exit code 1
                # Since somewhere between 3.7.9 and 3.10.4 the e.strerror does not contain the
                # missing file anymore, which makes it impossible to tell from the message, whether
                # the workdir is inaccessible, or the executed command.
                return Failed(execution_state,
                              UnixState.
                              as_external_state(None,
                                                None,
                                                1,
                                                "No such file or directory: " +
                                                repr(command.workdir)),
                              1)
            else:
                return Failed(execution_state,
                              UnixState.
                              as_external_state(None,
                                                None,
                                                127,
                                                "Command not executable: " +
                                                repr(effective_command.command_expression)),
                              127)
        except FileExistsError as e:
            raise NonRetryableExecutorError(f"Tried to rerun execution ID {execution_id}")

    def _retrieve_state_via_pid(self, pid: int)\
            -> Optional[ExternalState[UnixState]]:
        try:
            with self.storage.open(f"/proc/{pid}/stat", "r") as stat_fh:
                status_line = stat_fh.readlines()[0].rstrip()
                the_match = re.match(r"^(\d+)\s\((.+?)\)\s(\w+)((?:\s\d+){49})$",
                                     status_line)
                if the_match is not None:
                    state_code = the_match[2]
                    return UnixState.as_external_state(ProcessId(str(pid)), state_code, None, None)
                else:
                    # This should not happen. The file format is pretty fixed. If we can open the
                    # file, then we should also be able to parse it.
                    raise NonRetryableExecutorError("Could not parse process ID from "
                                                    f"'/proc/{pid}/stat: {status_line}")
        except FileNotFoundError:
            # No active process for PID. This may be because the process has already ended.
            return None
        except TypeError | IndexError as e:
            # This happens, if the status could not be read.
            raise NonRetryableExecutorError("Could not parse process ID from "
                                            f"'/proc/{pid}/stat: {status_line}")

    def _retrieve_state_via_execution_id(self, execution_id: WESkitExecutionId)\
            -> Optional[ExternalState[UnixState]]:
        """
        This searches for a process ID with the matching `weskit_execution_id` environment
        variable.
        """
        pid: Optional[str] = None
        for env_file in glob.glob("/proc/*/environ"):
            try:
                with self.storage.open(env_file, "r") as fh:
                    for varval in fh.readlines()[0].split("\000"):
                        m = re.match(rf"^{Executor.EXECUTION_ID_VARIABLE}={execution_id}$",
                                     varval)
                        if m is not None:
                            _, pid, _ = env_file.split("/")
            except PermissionError | FileNotFoundError | IndexError:
                # Ignore the error. Just skip to the next file.
                # Inbetween the glob and the file-open the file may have vanished. Also ignore
                # this, because it just means that process ended.
                pass
        if pid is not None:
            # We just parse the state using this found PID. It is possible that the process
            # ended in the meantime, but that's just how it is. We return the state then as
            # that state.
            return self._retrieve_state_via_pid(int(pid))
        else:
            return None

    def _retrieve_state_via_logdir(self, log_dir: Path)\
            -> Optional[ExternalState[UnixState]]:
        """
        This function assumes that no information is in the /proc filesystem. The only
        option then is to retrieve the state from the log-files produced by the wrapper script.
        """
        # Using the default files defined in `scripts/wrap`.
        log_file = log_dir / "pid"
        exit_code_file = log_dir / "exit_code"
        try:
            with self.storage.open(log_file, "r") as pid_fh:
                pid = int(pid_fh.readlines()[0])

            with self.storage.open(exit_code_file, "r") as exit_fh:
                # The exit code may only be empty, if the process still runs (which we exclude
                # as pre-condition, see comment), or another severe error prevented the exit code
                # from being written, and probably also the process did not end gracefully (e.g.
                # by server crash). All these are fatal system errors
                exit_code = int(exit_fh.readlines()[0])

            return UnixState.as_external_state(ProcessId(str(pid)),
                                               None,
                                               exit_code,
                                               "Process not in /proc")

        except IndexError | ValueError:
            # Corrupt pid file.
            return None
        except FileNotFoundError:
            # If the pid file is not found, then the log_dir is either wrong, or the process
            # ended even before the wrapper script was correctly started. We assume it is the
            # latter.
            return None
        except PermissionError as e:
            raise NonRetryableExecutorError(f"No permission to open {log_file}")

    def get_status(self,
                   execution_id: WESkitExecutionId,
                   log_dir: Optional[Url] = None,
                   pid: Optional[int] = None) \
            -> Optional[ExternalState[UnixState]]:
        """
        If the PID is provided, try to get the information using the PID

        Otherwise, try to recover the running process with the `weskit_execution_id` (that is
        set as environment variable `weskit_execution_id` on the process).

        If that fails, assume the process has ended (or was never started). Then try to retrieve
        the information from the execution log on the filesystem.

        If no information can be found there, return None. This should be interpreted as
        a system error in the executor for which the process information con not be recovered
        anymore.
        """
        if pid is not None:
            result = self._retrieve_state_via_pid(pid)
        else:
            result = self._retrieve_state_via_execution_id(execution_id)
        if result is None and log_dir is not None:
            result = self._retrieve_state_via_logdir(self._file_url_to_path(log_dir))
        return result

    def update_status(self,
                      current_state: ExecutionState[S],
                      log_dir: Optional[Url] = None,
                      pid: Optional[int] = None) \
            -> Optional[ExecutionState[S]]:
        """
        Update the executed process, if possible.
        """
        external_state = self.get_status(current_state.execution_id, log_dir, pid)
        if external_state is not None:
            return UnixExecutor._map_to_next_state(current_state, external_state)
        else:
            return None

    @abstractmethod
    def kill(self,
             state: ExecutionState[S],
             signal: Signals = Signals.SIGINT) -> bool:
        """
        Send a signal to the process with the given state. The signal should generally be
        termination signal (e.g. SIGKILL, SIGINT, etc.) -- any signal issued with the intention
        to terminate the process.

        If the state is already terminated, simply succeed. Obviously, this does not mean that
        the process was indeed terminated by the signal, but generally, that it was terminated.

        If the state was never observed, then fail. You first need to update the state.

        You can choose the signal. By default, it tries to terminate the process with SIGINT
        to emulate a keyboard-based interrupt. This should give the process the chance for a
        controlled exit. Check a list af Unix signals, to learn about alternatives
        (`man 7 signal`).
        """
        pass
