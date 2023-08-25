# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import os
import shlex
import tempfile
import uuid
from os import PathLike
from pathlib import Path
from subprocess import DEVNULL  # nosec: B404
from typing import Optional, cast

from asyncssh import SSHClientProcess, \
    SSHCompletedProcess
from urllib3.util import Url

from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.ExecutionState import ExecutionState, Start
from weskit.classes.executor.Executor \
    import ExecutionSettings
from weskit.classes.executor.ProcessId import WESkitExecutionId
from weskit.classes.executor.unix.UnixExecutor import UnixExecutor
from weskit.classes.executor.unix.UnixStates import UnixState
from weskit.classes.storage.SshStorageAccessor import SshStorageAccessor

logger = logging.getLogger(__name__)


class SshExecutor(UnixExecutor):
    """
    Execute commands via SSH on a remote host. Only key-based authentication is supported.

    This class uses asyncssh. You may want to set parameters during development.
    See https://docs.python.org/3/library/asyncio-dev.html#debug-mode.
    """

    def __init__(self,
                 connection: RetryableSshConnection,
                 log_dir_base: Optional[Path] = None):  # nosec B108
        super().__init__(SshStorageAccessor(connection),
                         log_dir_base)
        self._executor_id = uuid.uuid4()
        self._connection = connection

    @property
    def storage(self) -> SshStorageAccessor:
        return cast(SshStorageAccessor, super().storage)

    @property
    def hostname(self) -> str:
        return self._connection.hostname

    async def _create_env_script_locally(self,
                                         execution_id: WESkitExecutionId,
                                         command: ShellCommand)\
            -> Path:
        """
        Create an environment file with the variables requested via the command.

        Unless AcceptEnv or PermitUserEnvironment are configured in the sshd_config of
        the server, environment variables to be set for the target process cannot be used
        with the standard SSH-client code (e.g. via the env-parameter). For this reason,
        we create a remote temporary file on the remote host, that is sourced before the
        actual command is executed remotely.
        """
        file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False)
        self._create_env_script(file.name,
                                execution_id,
                                command.environment)
        return Path(file.name)

    async def _stage_remote_files(self,
                                  execution_id: WESkitExecutionId,
                                  command: ShellCommand):
        """
        Stage the environment requested by the command (as file) and the wrapper script that
        wraps the execution of the command, including changing the workdir and reading the
        environment. The remote target directory is the logging directory for the process.
        """
        log_dir = self._command_log_dir(execution_id, command)
        local_env_file: Optional[Path] = None
        try:
            local_env_file = await self._create_env_script_locally(execution_id, command)
            async with self._connection.context():
                # Note: If the remote log dir exists this means that the execution_id was reused. The
                #       execution_id, however should be used for a single execution attempt only!
                await self.storage.create_dir(log_dir,
                                              mode=0o750,
                                              exists_ok=False)
                await self.storage.put(local_env_file,
                                       self._env_path(log_dir),
                                       dirs_exist_ok=True)
                await self.storage.put(self._wrapper_source_path,
                                       self._wrapper_path(log_dir),
                                       dirs_exist_ok=True)
        finally:
            if local_env_file is not None:
                os.unlink(local_env_file)

    async def _is_executable(self, path: PathLike) -> bool:
        """
        Given the remote path of a file, check whether the file is executable for the logged-in
        user.
        """
        # `which` only returns exit code 0, if the provided argument -- with or without path --
        # is executable.
        async with self._connection.context():
            result: SSHCompletedProcess = \
                await self._connection.run(f"which {shlex.quote(str(path))}")
        return result.returncode == 0

    async def execute(self,
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
        log_dir = self._command_log_dir(execution_id, command)
        try:
            async with self._connection.context():
                await self._stage_remote_files(execution_id, effective_command)

                # SSH is always associated with a shell. Therefore, a *string* is processed by
                # asyncssh, rather than a list of strings. Therefore, we use the command_expression here.
                process: SSHClientProcess = await self._connection. \
                    create_process(command=effective_command.command_expression,
                                   # Ignore the standard streams. The wrapper writes to log files.
                                   stdout=DEVNULL,
                                   stderr=DEVNULL,
                                   stdin=DEVNULL,
                                   **kwargs)

                # The process already was sent to the background. We recover the process information.
                execution_state = await self.update_status(execution_state,
                                                           Url(scheme="file",
                                                               path=str(log_dir)))
                logger.debug(f"Executor {self.id} started process {execution_id} with PID " +
                             f"{execution_state.last_known_external_state.pid}: {effective_command}")
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

    async def kill(self, execution_state: ExecutionState[UnixState]) -> bool:
        process: SSHClientProcess = await self._connection. \
            create_process(command=f"kill -s SIGINT {execution_state.external_pid}")
        process.wait()
        if process.returncode == 1:
            # TODO if kill fails, process most likely has ended already. Check that the result files
            #      contain the exit code. Only then return True. Otherwise, something else may have
            #      gone wrong (tampered with process ID? Wrong host?). Then return False.
            return True

    async def wait(self, execution_state: ExecutionState[UnixState]) -> None:
        process: SSHClientProcess = await self._connection. \
            create_process(command=f"wait {execution_state.external_pid}")
        process.wait()