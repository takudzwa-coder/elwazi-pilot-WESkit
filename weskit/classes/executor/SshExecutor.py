#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from os import PathLike

import asyncio
import asyncssh
import logging
import os
import shlex
import tempfile
import uuid
from asyncssh import SSHClientConnection, SSHKey, SSHClientProcess, \
    ProcessError, SSHCompletedProcess
from contextlib import asynccontextmanager
from pathlib import Path
from subprocess import PIPE      # nosec: B404
from tenacity import \
    wait_exponential, stop_after_attempt, wait_random, AsyncRetrying, retry_if_exception
from typing import Optional, Sequence, Union, List

from weskit.classes.ShellCommand import ShellCommand, ss, ShellSpecial
from weskit.classes.executor.Executor \
    import Executor, ExecutionSettings, ExecutedProcess, \
    CommandResult, ExecutionStatus, ProcessId, FileRepr
from weskit.classes.executor.ExecutorException import \
    ExecutorException, ExecutionError, ConnectionError
from weskit.utils import now

logger = logging.getLogger(__name__)


def is_connection_interrupted(exception: BaseException) -> bool:
    return isinstance(exception, asyncssh.ChannelOpenError) and \
           exception.reason in ["SSH connection closed", "SSH connection lost"]


class SshExecutor(Executor):
    """
    Execute commands via SSH on a remote host. Only key-based authentication is supported.

    This class uses asyncssh. You may want to set parameters during development.
    See https://docs.python.org/3/library/asyncio-dev.html#debug-mode.
    """

    def __init__(self,
                 username: str,
                 hostname: str,
                 keyfile: PathLike,
                 keyfile_passphrase: str,
                 knownhosts_file: PathLike,
                 connection_timeout: str = "2m",
                 keepalive_interval: str = "0",
                 keepalive_count_max: int = 3,
                 port: int = 22,
                 retry_options: dict = None,
                 remote_tmp_base: Path = Path("/tmp/weskit/ssh")):  # nosec B108
        """
        Keepalive: This is for a server application. The default is to have a keep-alive, but one
                   that allows recovery after even a long downtime of the remote host.

        :param username: Remote SSH user name.
        :param hostname: Remote host.
        :param keyfile: Only key-based authentication is supported.
        :param keyfile_passphrase: The passphrase to use for the keyfile.
        :param knownhosts_file: Path to a knownHosts file to authenticate the server side.
        :param connection_timeout: The timeout for establishing a new connection.
        :param keepalive_interval: How frequently the connection state shall be checked.
        :param keepalive_count_max: The number of tries, in case the connection cannot be verified.
        :param port: Defaults to standard SSH-port 22.
        """
        self._username = username
        self._hostname = hostname
        self._keyfile = keyfile
        self._keyfile_passphrase = keyfile_passphrase
        self._port = port
        self._connection_timeout = connection_timeout
        self._keepalive_interval = keepalive_interval
        self._keepalive_count_max = keepalive_count_max
        self._knownhosts_file = knownhosts_file
        self._executor_id = uuid.uuid4()
        try:
            self._event_loop = asyncio.get_event_loop()
        except RuntimeError as ex:
            # Compare StackOverflow: https://tinyurl.com/yckkwbew
            if str(ex).startswith('There is no current event loop in thread'):
                logger.warning("Using a fresh asyncio event-loop")
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
            else:
                raise ex

        self._remote_tmp = remote_tmp_base

        if retry_options is None:
            retry_options = {
                "wait_exponential": {
                    "multiplier": 1,
                    "min": 4,
                    "max": 300
                },
                "wait_random": {
                    "min": 0,
                    "max": 1
                },
                "stop_after_attempt": 5
            }
        self._retry_options = {
            # By default, do exponential backoff with jitter, to avoid synchronous reconnection
            # attempts by synchronously affected connections.
            "wait":
                wait_exponential(**retry_options["wait_exponential"]) +
                wait_random(**retry_options["wait_random"]),
            "stop":
                stop_after_attempt(retry_options["stop_after_attempt"])
        }

        self._connect()

    def _reconnection_retry_options(self, **kwargs) -> dict:
        """
        All retries should wrap around external asynchronous calls, such as asyncssh, or
        async functions that themselves do no retry, because errors are simply re-raised.
        Thus, if the same error is causing a retry at different levels, retry attempts multiply!
        """
        return {**self._retry_options,
                "reraise": True,
                "retry": retry_if_exception(is_connection_interrupted),
                "after": self._connection,
                **kwargs}

    @asynccontextmanager
    async def _retryable_connection(self, **kwargs):
        """
        A context manager that simplifies the calling of SSH operations with retry. You can add
        parameters to tenacity.AsyncRetrying to override any defaults.

        with self._retryable_connection():
            do_ssh_ap()

        Exceptions raised by asyncssh are wrapped in an ExecutorException.
        """
        try:
            async for attempt in AsyncRetrying(**self._reconnection_retry_options(**kwargs)):
                with attempt:
                    yield self
        except asyncssh.DisconnectError as e:
            raise ConnectionError("Disconnected", e)
        except asyncssh.ChannelOpenError as ex:
            raise ConnectionError("Channel open failed", ex)
        except asyncssh.Error as ex:
            raise ExecutorException("SSH error", ex)

    @property
    def username(self) -> str:
        return self._username

    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def port(self) -> int:
        return self._port

    @property
    def _remote_name(self) -> str:
        return f"{self.username}@{self.hostname}:{self.port}"

    @property
    def keyfile(self) -> PathLike:
        return self._keyfile

    def _connect(self) -> None:
        # Some related docs:
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-known-hosts
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-private-keys
        # * https://asyncssh.readthedocs.io/en/latest/api.html#sshclientconnectionoptions
        ssh_keys: Sequence[SSHKey] = asyncssh.read_private_key_list(Path(self._keyfile),
                                                                    self._keyfile_passphrase)
        logger.info(f"Read private keys from {self._keyfile}. " +
                    f"sha256 fingerprints: {list(map(lambda k: k.get_fingerprint(), ssh_keys))}")
        try:
            self._connection: SSHClientConnection = \
                self._event_loop.run_until_complete(
                    asyncssh.connect(host=self.hostname,
                                     port=self.port,
                                     username=self.username,
                                     client_keys=ssh_keys,
                                     known_hosts=str(self._knownhosts_file),
                                     login_timeout=self._connection_timeout,
                                     keepalive_interval=self._keepalive_interval,
                                     keepalive_count_max=self._keepalive_count_max,
                                     # By default do not forward the local environment.
                                     env={},
                                     send_env={}))
            logger.debug(f"Connected to {self._remote_name}")
        except asyncssh.DisconnectError as e:
            raise ExecutorException("Connection error (disconnect)", e)
        except asyncio.TimeoutError as e:
            raise ExecutorException("Connection error (timeout)", e)

    async def put(self, srcpath: PathLike, dstpath: PathLike, **kwargs):
        async with self._retryable_connection():
            await asyncssh.scp(srcpaths=str(srcpath),
                               dstpath=(self._connection, str(dstpath)), **kwargs)

    async def get(self, srcpath: PathLike, dstpath: PathLike, **kwargs):
        async with self._retryable_connection():
            await asyncssh.scp(srcpaths=(self._connection, str(srcpath)),
                               dstpath=str(dstpath), **kwargs)

    async def remote_rm(self, path: Path):
        async with self._retryable_connection():
            await self._connection.run(f"rm {shlex.quote(str(path))}")

    def _process_directory(self, process_id: uuid.UUID) -> Path:
        return self._remote_tmp / str(self._executor_id) / str(process_id)  # nosec: B108

    def _env_path(self, process_id: uuid.UUID) -> Path:
        return self._process_directory(process_id) / "wrapper.sh"

    async def _create_wrapper(self, command: ShellCommand) -> Path:
        """
        We assume Bash is available on the remote side. Detection of the shell is tricky, if at all
        possible. Therefore, if you want to support other shells, make this configurable via a
        WESkit variable.

        The protocol is

                source wrapper.sh && command arg1 arg2 ...
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
        local_env_file = await self._create_wrapper(command)
        remote_dir = self._process_directory(process_id)
        try:
            async with self._retryable_connection():
                await self._connection.\
                    run(f"set -ue; umask 0077; mkdir -p {shlex.quote(str(remote_dir))}", check=True)

                # We use run() rather than sftp, because sftp is not turned on all SSH servers.
                await asyncssh.scp(local_env_file,
                                   (self._connection, self._env_path(process_id)))
        finally:
            os.unlink(local_env_file)

    async def _is_executable(self, path: PathLike) -> bool:
        """
        Given the remote path of a file, check whether the file is executable for the logged-in
        user.
        """
        # `which` only returns exit code 0, if the provided argument -- with or without path --
        # is executable.
        async with self._retryable_connection():
            result: SSHCompletedProcess = \
                await self._connection.run(f"which {shlex.quote(str(path))}")
        return result.returncode == 0

    async def _upload_file(self, local_path: Path, remote_path: Path):
        """
        We can't assume that local and remote path are identical. Thus file upload
        has to go into a manually generated remote folder.

        :param local_path:
        :param remote_path:
        :return:
        """
        try:
            async with self._retryable_connection():
                await asyncssh.scp(str(local_path), (self._connection, str(remote_path)))
        finally:
            os.unlink(local_path)

    def copy_file(self, source: Path, target: Path):
        self._event_loop.run_until_complete(self._upload_file(source, target))

    def remove_file(self, target: Path):
        self._event_loop.run_until_complete(self.remote_rm(target))

    async def _execute(self,
                       command: ShellCommand,
                       stdout_file: Optional[FileRepr] = None,
                       stderr_file: Optional[FileRepr] = None,
                       stdin_file: Optional[FileRepr] = None,
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
        process_id = uuid.uuid4()

        # Unless AcceptEnv or PermitUserEnvironment are configured in the sshd_config of
        # the server, environment variables to be set for the target process cannot be used
        # with the standard SSH-client code (e.g. via the env-parameter). For this reason,
        # we create a remote temporary file on the remote host, that is sourced before the
        # actual command is executed remotely.
        await self._upload_env(process_id, command)

        # SSH is always associated with a shell. Therefore, a string is processed by asyncssh,
        # rather than an executable with a sequence of parameters, all in a list (compare
        # subprocess.run/Popen).
        #
        # The environment setup script is `source`d.
        source_prefix: List[Union[str, ShellSpecial]] = \
            ["source", str(self._env_path(process_id)), ss("&&")]
        effective_command = \
            command.copy(command=source_prefix + command.command)

        async with self._retryable_connection():
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
                                                        id=ProcessId(process_id),
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
        try:
            async with self._retryable_connection():
                await process.handle.wait()
                self.update_process(process)
                wrapper_path = self._env_path(process.id.value)
                await self._connection.run(f"rm {shlex.quote(str(wrapper_path))}", check=True)
                process_dir = self._process_directory(process.id.value)
                await self._connection.run(f"rmdir {shlex.quote(str(process_dir))}", check=True)
        except TimeoutError as e:
            raise ExecutionError(f"Process {process.id.value} timed out:" +
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
            raise ExecutionError(f"Could not kill process ({process.command.command})", e)
