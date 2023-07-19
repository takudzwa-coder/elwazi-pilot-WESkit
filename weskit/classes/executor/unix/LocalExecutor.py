# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import os
import socket
import subprocess  # nosec B603 B404
from builtins import super, property
from pathlib import Path
from signal import Signals
from typing import Optional, TypeVar, Generic, cast

from urllib3.util.url import Url

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.ExecutionState import ExecutionState, Failed, Start
from weskit.classes.executor.Executor import Executor, ExecutionSettings
from weskit.classes.executor.ExecutorError import NonRetryableExecutorError
from weskit.classes.executor.ProcessId import WESkitExecutionId
from weskit.classes.executor.unix.UnixExecutor import UnixExecutor
from weskit.classes.executor.unix.UnixStates import UnixState, UnixStateMapper
from weskit.classes.storage.LocalStorageAccessor import LocalStorageAccessor

logger = logging.getLogger(__name__)


S = TypeVar("S")


class LocalExecutor(Generic[S], UnixExecutor[S]):
    """
    Execute commands locally. The commands are executed asynchronously in the background managed
    by the operating system. Therefore, there is no asynchronous job management here.
    """

    _map_to_next_state = UnixStateMapper()

    def __init__(self):
        super().__init__(LocalStorageAccessor())

    @property
    def storage(self) -> LocalStorageAccessor:
        return cast(LocalStorageAccessor, super().storage)

    @property
    def hostname(self) -> str:
        """
        The service is supposed to be run in containers. It does not make sense to return
        "localhost" (on which host is this code running?). By contrast, the container name
        might be useful.
        """
        return socket.gethostname()

    @property
    def _wrapper_path(self, stage_dir: Optional[Path] = None) -> Path:
        return self._wrapper_source_path

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
            self.storage.create_dir(log_dir, exists_ok=False, mode=0o750)

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
            logger.debug(f"Executor {self.id} started process {execution_id} with PID " +
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

    def kill(self,
             state: ExecutionState[S],
             signal: Signals = Signals.SIGINT) -> bool:
        if state.is_terminal:
            return True
        elif not state.ever_observed:
            return False
        else:
            pid = int(state.last_known_external_state.pid.value)
            os.kill(pid, signal)
            return True
