# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import socket
import subprocess  # nosec B603 B404
from os import PathLike

from builtins import int, super, open, property
from typing import Optional, cast, IO, Union, List

import weskit.classes.executor.Executor as base
from weskit.classes.ShellCommand import ShellCommand, ShellSpecial, ss
from weskit.classes.storage.LocalStorageAccessor import LocalStorageAccessor
from weskit.utils import now

logger = logging.getLogger(__name__)


class LocalExecutor(base.Executor):
    """
    Execute commands locally. The commands are executed asynchronously in the background managed
    by the operating system. Therefore, there is no asynchronous job management here.
    """

    def __init__(self):
        super().__init__()
        self._storage = LocalStorageAccessor()

    @property
    def storage(self) -> LocalStorageAccessor:
        return self._storage

    @property
    def hostname(self) -> str:
        """
        The service is supposed to be run in containers. It does not make sense to return
        "localhost" (on which host is this code running?). By contrast, the container name
        might be useful.
        """
        return socket.gethostname()

    def execute(self,
                command: ShellCommand,
                wid: Optional[base.WESkitProcessId] = None,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[base.ExecutionSettings] = None,
                **kwargs) \
            -> base.ExecutedProcess:
        """
        Execute the process in the background and return the process ID.

        The command is always wrapped in Bash shell.
        """
        if wid is None:
            wid = base.WESkitProcessId()

        start_time = now()

        effective_command: List[Union[str, ShellSpecial]] = \
            ["bash", "-c", command.command_expression]

        # TODO Wrapper script with redirections, pid!

        try:
            process = subprocess.run(effective_command,
                                     cwd=command.workdir,
                                     env={
                                         "weskit_process_id": str(wid),
                                         **command.environment
                                     },
                                     shell=False,    # We wrap in Bash.
                                     **kwargs)
            logger.debug(f"Started process {process.pid}: {effective_command}")

            return base.ExecutedProcess(executor=self,
                                        weskit_id=wid,
                                        pre_result=base.
                                        CommandResult(command=command,
                                                      process_id=base.ProcessId(process.pid),
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      stdin_file=stdin_file,
                                                      execution_status=base.ExecutionStatus(),
                                                      start_time=start_time))
        except FileNotFoundError as e:
            # The other executors recognize inaccessible working directories or missing commands
            # only after the wait_for(). We emulate this behaviour here such that all executors
            # behave identically with respect to these problems.
            if str(e).startswith(f"[Errno 2] No such file or directory: {repr(command.workdir)}"):
                # cd /dir/does/not/exist: exit code 1
                # Since somewhere between 3.7.9 and 3.10.4 the e.strerror does not contain the
                # missing file anymore, which makes it impossible to tell from the message, whether
                # the workdir is inaccessible, or the executed command.
                exit_code = 1
            else:
                # Command not executable: exit code 127
                exit_code = 127

            return base.ExecutedProcess(executor=self,
                                        process_handle=None,
                                        pre_result=base.
                                        CommandResult(command=command,
                                                      process_id=base.ProcessId(None),
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      stdin_file=stdin_file,
                                                      execution_status=base.ExecutionStatus(
                                                          exit_code, message=e.strerror),
                                                      start_time=start_time))

    def get_status(self, process: base.ExecutedProcess) -> base.ExecutionStatus:
        if process.handle is None:
            return process.result.status
        else:
            return base.ExecutionStatus(process.handle.poll())

    def update_process(self, process: base.ExecutedProcess) -> base.ExecutedProcess:
        """
        Update the executed process, if possible.
        """
        if process.handle is None:
            # There is no process handle. We cannot update the result.
            return process
        else:
            result = process.result
            return_code = process.handle.poll()
            if return_code is not None:
                result.status = base.ExecutionStatus(return_code)
                result.end_time = now()
                process.result = result
        return process

    def kill(self, process: base.ExecutedProcess):
        if process.handle is not None:
            process.handle.terminate()
        # TODO The API says little. The code says it uses os.kill for Unix. More recherche needed.

    def wait_for(self, process: base.ExecutedProcess, timeout: Optional[float] = None)\
            -> base.CommandResult:
        if not process.result.status.finished:
            return_code = process.handle.wait(timeout)
            if return_code is None:
                raise RuntimeError(
                    f"subprocess.wait() should not return None (pid={process.handle.pid})")
            process.result.status = base.ExecutionStatus(return_code)
            process.result.end_time = now()
        return process.result
