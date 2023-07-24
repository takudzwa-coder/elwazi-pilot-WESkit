# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import os
import shlex
import tempfile
import uuid
from asyncio import AbstractEventLoop
from os import PathLike
from pathlib import Path
from subprocess import PIPE  # nosec: B404
from typing import Optional, Union, List, cast

from asyncssh import SSHClientProcess, \
    SSHCompletedProcess
from urllib3.util import Url

from classes.executor.ProcessId import WESkitExecutionId
from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.ShellCommand import ShellCommand, ss, ShellSpecial
from weskit.classes.executor.ExecutionState import ExecutionState, Start
from weskit.classes.executor.Executor \
    import ExecutionSettings
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
                 event_loop: Optional[AbstractEventLoop] = None):  # nosec B108
        super().__init__(SshStorageAccessor(connection),
                         event_loop)
        self._executor_id = uuid.uuid4()
        self._connection = connection

    @property
    def storage(self) -> SshStorageAccessor:
        return cast(SshStorageAccessor, super().storage)

    @property
    def hostname(self) -> str:
        return self._connection.hostname

    def _env_path(self, execution_id: WESkitExecutionId) -> Path:
        return self._process_directory(execution_id) / "env.sh"

    def _wrapper_path(self, stage_path: Optional[Path]) -> Path:
        if stage_path is None:
            raise RuntimeError("Oops! No staging directory provided")
        else:
            return stage_path / "wrap"

    async def _create_env_script(self, command: ShellCommand) -> Path:
        """
        We assume Bash is available on the remote side. Detection of the shell is tricky, if at all
        possible. Therefore, if you want to support other shells, make this configurable via a
        WESkit variable.

        The protocol is

                source env.sh && command arg1 arg2 ...
        """
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
            print("#!/bin/bash", file=file)
            # Whatever command is executed later, make sure to catch all errors. This is also
            # important for the `cd`, which may fail if the working directory is not
            # accessible.
            print("set -o pipefail -ue", file=file)
            print("echo 'Current working directory:' $PWD", file=file)
            if command.workdir is not None:
                print(f"cd {shlex.quote(str(command.workdir))}", file=file)
            for var_name, var_value in command.environment.items():
                print(f"export {var_name}={shlex.quote(var_value)}", file=file)
            return Path(file.name)

    async def _stage_helper_scripts(self,
                                    execution_id: WESkitExecutionId,
                                    command: ShellCommand):
        """
        SSH usually does not allow to set environment variables. Therefore, we create a little
        script that sets up the environment for the remote process.

        The usage protocol is

            source env.sh && command arg1 ...

        :param command:
        :return:
        """
        local_env_file = await self._create_env_script(command)
        remote_dir = self._process_directory(execution_id)
        try:
            async with self._connection.context():
                await self.storage.create_dir(remote_dir,
                                              mode=0o0770,
                                              exists_ok=True)
                await self.storage.put(local_env_file,
                                       self._env_path(execution_id),
                                       dirs_exist_ok=True)
                await self.storage.put(self._wrapper_source_path,
                                       self._wrapper_path(...TODO...),
                                       dirs_exist_ok=True)
        finally:
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

    def execute(self, *args, **kwargs) \
            -> ExecutionState[UnixState]:
        return self._event_loop.run_until_complete(self._execute(*args, **kwargs))

    async def _execute(self,
                       execution_id: WESkitExecutionId,
                       command: ShellCommand,
                       stdout_url: Optional[Url] = None,
                       stderr_url: Optional[Url] = None,
                       stdin_url: Optional[Url] = None,
                       settings: Optional[ExecutionSettings] = None,
                       **kwargs) \
            -> ExecutionState[UnixState]:
        """
        Only client-side stdout/stderr/stdin-files are supported. If you want that standard input,
        output and error refer to remote files, then include them into the command (e.g. with
        shell redirections).

        :param command:
        :param stdout_url:
        :param stderr_url:
        :param stdin_url:
        :param settings:
        :return:
        """
        # Unless AcceptEnv or PermitUserEnvironment are configured in the sshd_config of
        # the server, environment variables to be set for the target process cannot be used
        # with the standard SSH-client code (e.g. via the env-parameter). For this reason,
        # we create a remote temporary file on the remote host, that is sourced before the
        # actual command is executed remotely.

        effective_command = self._wrapped_command(execution_id,
                                                  command,
                                                  stdout_url,
                                                  stderr_url,
                                                  stdin_url)
        execution_state = Start(execution_id)
        log_dir = self._log_dir(command.workdir, execution_id)
        try:
           async with self._connection.context():

                # PREPARE INPUTS
                # Note: If the log dir exists this means that the execution_id was reused. The
                #       execution_id, however should be used for a single execution attempt only!
                await self.storage.create_dir(log_dir, exists_ok=False, mode=0o750)

                await self.storage.put(self._wrapper_source_path,
                                       self._wrapper_path(log_dir))

                # TODO copy the environment file. Remove the "helper" script to the log_dir.
                # TODO add the environment file as env parameter to the wrapper call.
                await self._stage_helper_scripts(execution_id, effective_command)

                # RUN PROCESS
                # SSH is always associated with a shell. Therefore, a *string* is processed by
                # asyncssh, rather than a list of strings like for subprocess.run/Popen). Therefore,
                # we use the command_expression here.
                process: SSHClientProcess = await self._connection. \
                    create_process(command=effective_command.command_expression,
                                   stdout=PIPE,
                                   stderr=PIPE,
                                   **kwargs)
                    # TODO cwd=command.workdir,
                    # TODO env={
                           # Tag the process with `weskit_process_id` to make it
                           # recoverable with a query of the environment variables
                           # # of process (e.g. on /proc/).
                           # Executor.EXECUTION_ID_VARIABLE: str(execution_id),
                           # **command.environment
                           # }
                # TODO Read stdin and stderr of submission process for error-tracking. Get wrapper's JSON output.


                # TODO Do we want to update from the process? Or just use the stdout from the wrapper?
                # The process already was sent to the background. We recover the process information.
                execution_state = self.update_status(execution_state,
                                                     Url(scheme="file",
                                                         path=str(log_dir)),
                                                     process.pid???)
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


    def kill(self, execution_state: ExecutionState[UnixState]) -> bool:
        pass
        # TODO Invoke `kill -s SIGINT` remotely.
