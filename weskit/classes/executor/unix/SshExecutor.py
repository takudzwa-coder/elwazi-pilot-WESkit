#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import os
import shlex
import tempfile
import uuid
from asyncio import AbstractEventLoop
from os import PathLike
from pathlib import Path
from subprocess import PIPE  # nosec: B404
from typing import Optional, Union, List

from asyncssh import SSHClientProcess, \
    ProcessError, SSHCompletedProcess

from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.ShellCommand import ShellCommand, ss, ShellSpecial
from weskit.classes.executor.Executor \
    import Executor, ExecutionSettings, ExecutedProcess, \
    CommandResult, ExecutionStatus, ProcessId
from weskit.classes.executor.ExecutorException import \
    ExecutorException, ProcessingError
from weskit.classes.storage.SshStorageAccessor import SshStorageAccessor
from weskit.utils import now

logger = logging.getLogger(__name__)


class SshExecutor(Executor):
    """
    Execute commands via SSH on a remote host. Only key-based authentication is supported.

    This class uses asyncssh. You may want to set parameters during development.
    See https://docs.python.org/3/library/asyncio-dev.html#debug-mode.
    """

    def __init__(self,
                 connection: RetryableSshConnection,
                 event_loop: Optional[AbstractEventLoop] = None,
                 remote_tmp_base: Path = Path("/tmp/weskit/ssh")):  # nosec B108
        super().__init__(event_loop)
        self._executor_id = uuid.uuid4()
        self._remote_tmp = remote_tmp_base
        self._connection = connection
        self._storage = SshStorageAccessor(connection)

    @property
    def storage(self) -> SshStorageAccessor:
        return self._storage

    @property
    def hostname(self) -> str:
        return self._connection.hostname

    def _process_directory(self, process_id: uuid.UUID) -> Path:
        return self._remote_tmp / str(self._executor_id) / str(process_id)  # nosec: B108

    def _env_path(self, process_tag: uuid.UUID) -> Path:
        return self._process_directory(process_tag) / "env.sh"

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
            print("set -o pipefail -ue", file=file)
            if command.workdir is not None:
                # Whatever command is executed later, make sure to catch all errors. This is also
                # important for the `cd`, which may fail if the working directory is not
                # accessible.
                print(f"cd {shlex.quote(str(command.workdir))}", file=file)
            for var_name, var_value in command.environment.items():
                print(f"export {var_name}={shlex.quote(var_value)}", file=file)
            return Path(file.name)

    async def _upload_env(self, process_id: uuid.UUID, command: ShellCommand):
        """
        SSH usually does not allow to set environment variables. Therefore, we create a little
        script that sets up the environment for the remote process.

        The environment script will be put into a directory that uniquely identifies the process
        and uses information about the parent process (the one running the SSHExecutor).

        The usage protocol is

            source env.sh && command arg1 ...

        :param command:
        :return:
        """
        local_env_file = await self._create_env_script(command)
        remote_dir = self._process_directory(process_id)
        try:
            async with self._connection.context():
                await self.storage.create_dir(remote_dir,
                                              mode=0o077,
                                              exists_ok=True)
                await self.storage.put(local_env_file,
                                       self._env_path(process_id),
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

    async def _execute(self,
                       command: ShellCommand,
                       stdout_file: Optional[PathLike] = None,
                       stderr_file: Optional[PathLike] = None,
                       stdin_file: Optional[PathLike] = None,
                       settings: Optional[ExecutionSettings] = None,
                       **kwargs) -> ExecutedProcess:
        """
        Only client-side stdout/stderr/stdin-files are supported. If you want that standard input,
        output and error refer to remote files, then include them into the command (e.g. with
        shell redirections).

        :param command:
        :param stdout_file:
        :param stderr_file:
        :param stdin_file:
        :param settings:
        :return:
        """
        start_time = now()
        # Note that the process tag according to the settings.tag field and this process_id are
        # intentionally kept distinct, like they are also for all the other `Executor` classes.
        process_id = uuid.uuid4()

        # Unless AcceptEnv or PermitUserEnvironment are configured in the sshd_config of
        # the server, environment variables to be set for the target process cannot be used
        # with the standard SSH-client code (e.g. via the env-parameter). For this reason,
        # we create a remote temporary file on the remote host, that is sourced before the
        # actual command is executed remotely.
        source_prefix: List[Union[str, ShellSpecial]] = \
            ["source", str(self._env_path(process_id)), ss("&&")]

        effective_command = \
            command.copy(command=source_prefix + command.command,
                         # The tag is also used to mark the process by an environment
                         # variable that can be retrieved from /proc/*/environ on the remote
                         # system.
                         environment=command.environment)

        await self._upload_env(process_id, effective_command)

        async with self._connection.context():
            # SSH is always associated with a shell. Therefore, a *string* is processed by
            # asyncssh, rather than a list of strings like for subprocess.run/Popen). Therefore,
            # we use the command_expression here.
            process: SSHClientProcess = await self._connection.\
                create_process(command=effective_command.command_expression,
                               stdin=PIPE if stdin_file is None else stdin_file,
                               stdout=PIPE if stdout_file is None else stdout_file,
                               stderr=PIPE if stderr_file is None else stderr_file,
                               **kwargs)
        logger.info(f"Executed command ({process_id}): {effective_command.command_expression}")

        return ExecutedProcess(executor=self,
                               process_handle=process,
                               pre_result=CommandResult(command=command,
                                                        process_id=ProcessId(process_id),
                                                        stdout_file=stdout_file,
                                                        stderr_file=stderr_file,
                                                        stdin_file=stdin_file,
                                                        execution_status=ExecutionStatus(),
                                                        start_time=start_time))

    def execute(self, *args, **kwargs) -> ExecutedProcess:
        return self._event_loop.run_until_complete(self._execute(*args, **kwargs))

    def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
        return ExecutionStatus(process.handle.returncode)

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        """
        Update the executed process, if possible.
        """
        result = process.result
        return_code = process.handle.returncode
        if return_code is not None:
            result.status = ExecutionStatus(return_code)
            result.end_time = now()
            process.result = result
        return process

    async def _wait_for(self, process: ExecutedProcess) -> CommandResult:
        if process.id.value is None:
            raise RuntimeError("Process has no valid ID")
        else:
            try:
                async with self._connection.context():
                    await process.handle.wait()
                    self.update_process(process)
                    env_path = self._env_path(process.id.value)
                    await self.storage.remove_file(env_path)
                    process_dir = self._process_directory(process.id.value)
                    await self.storage.remove_dir(process_dir, recurse=True)
            except TimeoutError as e:
                raise ProcessingError(f"Process {process.id.value} timed out:" +
                                      str(process.command.command), e)
            except ProcessError as e:
                raise ExecutorException(f"Error during cleanup of {process.id.value}:" +
                                        str(process.command.command), e)
            return process.result

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        return self._event_loop.run_until_complete(self._wait_for(process))

    def kill(self, process: ExecutedProcess):
        try:
            process.handle.kill()
            self.wait_for(process)
        except OSError as e:
            raise ProcessingError(f"Could not kill process ({process.command.command})", e)
