#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import asyncio
import logging
import os
import shlex
import tempfile
import uuid
from asyncio.subprocess import PIPE
from datetime import datetime
from os import PathLike
from pathlib import PurePath
from typing import Optional, List

import asyncssh
from asyncssh import SSHClientConnection, SSHKey, SSHClientProcess, ChannelOpenError, \
    ProcessError, SSHCompletedProcess

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor \
    import Executor, ExecutionSettings, ExecutedProcess, \
    CommandResult, RunStatus, ProcessId, FileRepr
from weskit.classes.executor.ExecutorException import ExecutorException

logger = logging.getLogger(__name__)


class SshExecutor(Executor):
    """
    Execute commands via SSH on a remote host. Only key-based authentication is supported.

    This class uses asyncssh. You may want to set parameters during development.
    See https://docs.python.org/3/library/asyncio-dev.html#debug-mode.
    """

    def __init__(self, username: str,
                 hostname: str,
                 keyfile: PathLike,
                 keyfile_passphrase: str,
                 knownhosts_file: PathLike,
                 connection_timeout: str = "2m",
                 keepalive_interval: str = "0",
                 keepalive_count_max: int = 3,
                 port: int = 22):
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
        self._event_loop = asyncio.get_event_loop()
        self._connect()

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

    def _connect(self):
        # Some related docs:
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-known-hosts
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-private-keys
        # * https://asyncssh.readthedocs.io/en/latest/api.html#sshclientconnectionoptions
        ssh_keys: List[SSHKey] = asyncssh.read_private_key_list(self._keyfile,
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
                                     env={}, send_env={}))
            logger.debug(f"Connected to {self._remote_name}")
        except asyncssh.DisconnectError as e:
            raise ExecutorException("Connection error (disconnect)", e)
        except asyncio.TimeoutError as e:
            raise ExecutorException("Connection error (timeout)", e)

    async def put(self, srcpath: PathLike, dstpath: PathLike, **kwargs):
        await asyncssh.scp(srcpaths=srcpath, dstpath=(self._connection, dstpath), **kwargs)

    async def get(self, srcpath: PathLike, dstpath: PathLike, **kwargs):
        await asyncssh.scp(srcpaths=(self._connection, srcpath), dstpath=dstpath, **kwargs)

    async def remote_rm(self, path: PathLike):
        await self._connection.run(f"rm {shlex.quote(str(path))}")

    def _process_directory(self, process_id: uuid.UUID) -> PurePath:
        return PurePath("/tmp/weskit/ssh") / str(self._executor_id) / str(process_id)  # nosec: B108

    def _setup_script_path(self, process_id: uuid.UUID) -> PurePath:
        return self._process_directory(process_id) / "wrapper.sh"

    async def _create_setup_script(self, command: ShellCommand) -> PurePath:
        """
        We assume Bash is used on the remote side. Detection of the shell is tricky, if at all
        possible. Therefore, if you want to support other shells, make this configurable via a
        WESkit variable.
        """
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
            if command.workdir is not None:
                # Whatever command is executed later, make sure to catch all errors. This is also
                # important for the `cd`, which may fail if the working directory is not
                # accessible.
                print("set -o pipefail -ue", file=file)
                print(f"cd {shlex.quote(str(command.workdir))}", file=file)
            for export in [f"export {it[0]}={shlex.quote(it[1])}"
                           for it in command.environment.items()]:
                print(export, file=file)
            return PurePath(file.name)

    async def _upload_setup_script(self, process_id: uuid.UUID, command: ShellCommand):
        """
        SSH usually does not allow to set environment variables. Therefore, we create a little
        script that sets up the environment for the remote process.

        The wrapper will be put into a directory that uniquely identifies the process and uses
        information about the parent process (the one running the SSHExecutor).

        :param command:
        :return:
        """
        local_script_file = await self._create_setup_script(command)
        try:
            remote_dir = self._process_directory(process_id)
            await self._connection.\
                run(f"set -ue; umask 0077; mkdir -p {shlex.quote(str(remote_dir))}", check=True)

            # We use run() rather than sftp, because sftp is not turned on all SSH servers.
            await asyncssh.scp(local_script_file,
                               (self._connection, self._setup_script_path(process_id)))
        finally:
            await self._event_loop.run_in_executor(None, lambda: os.unlink(local_script_file))

    async def _is_executable(self, path: PathLike) -> bool:
        """
        Given the remote path of a file, check whether the file is executable for the logged-in
        user.
        """
        # `which` only returns exit code 0, if the provided argument -- with or without path --
        # is executable.
        result: SSHCompletedProcess = \
            await self._connection.run(f"which {shlex.quote(str(path))}")
        return result.returncode == 0

    async def _upload_file(self, local_path: PathLike, remote_path: PathLike):
        """
        We can't assume that local and remote path are identical. Thus file upload
        has to go into a manually generated remote folder.

        :param local_path:
        :param remote_path:
        :return:
        """
        try:
            await asyncssh.scp(local_path, (self._connection, remote_path))
        finally:
            await self._event_loop.run_in_executor(None, lambda: os.unlink(local_path))

    def copy_file(self, source: PathLike, target: PathLike):
        self._event_loop.run_until_complete(self._upload_file(source, target))

    def remove_file(self, target: PathLike):
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

        Note that if you want shell-variables present on the execution side (the shell started by
        connecting via SSH), then you need to wrap the actual command into `bash -c`. Otherwise
        variable references, such as `$someVar` are not evaluated in the remote shell. E.g. the
        following

          command = ["bash", "-c", "echo \"$someVar\""]
          environment = { "someVar": "Hello, World" }

        will result in the execution of `echo "Hello, World"` on the remote side.

        Note that the paths for the stdout, stderr, and stdin files are *remote* paths.

        :param command:
        :param stdout_file:
        :param stderr_file:
        :param stdin_file:
        :param settings:
        :return:
        """
        start_time = datetime.now()
        try:
            process_id = uuid.uuid4()
            # Unless AcceptEnv or PermitUserEnvironment are configured in the sshd_config of
            # the server, environment variables to be set for the target process cannot be used
            # with the standard SSH-client code (e.g. via the env-parameter). For this reason,
            # we create a remote temporary file on the remote host, that is loaded before the
            # actual command is executed remotely.
            await self._upload_setup_script(process_id, command)

            # SSH is always associated with a shell. Therefore a string is processed by asyncssh,
            # rather than an executable with a sequence of parameters, all in a list (compare
            # subprocess.run/Popen).
            #
            # The environment setup script is `source`d.
            effective_command = \
                ["source", shlex.quote(str(self._setup_script_path(process_id))), "&&"] + \
                ["sleep 1 &&"] + \
                list(map(shlex.quote, command.command))

            final_command_str = " ".join(effective_command)
            logger.debug(f"Executed command ({process_id}): {effective_command}")
            process: SSHClientProcess = await self._connection.\
                create_process(command=final_command_str,
                               stdin=PIPE if stdin_file is None else stdin_file,
                               stdout=PIPE if stdout_file is None else stdout_file,
                               stderr=PIPE if stderr_file is None else stderr_file,
                               **kwargs)
        except ChannelOpenError as e:
            raise ExecutorException("Couldn't execute process", e)

        return ExecutedProcess(executor=self,
                               process_handle=process,
                               pre_result=CommandResult(command=command,
                                                        id=ProcessId(process_id),
                                                        stdout_file=stdout_file,
                                                        stderr_file=stderr_file,
                                                        stdin_file=stdin_file,
                                                        run_status=RunStatus(),
                                                        start_time=start_time))

    def execute(self, *args, **kwargs) -> ExecutedProcess:
        return self._event_loop.run_until_complete(self._execute(*args, **kwargs))

    def get_status(self, process: ExecutedProcess) -> RunStatus:
        return RunStatus(process.handle.returncode)

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        """
        Update the executed process, if possible.
        """
        result = process.result
        return_code = process.handle.returncode
        if return_code is not None:
            result.status = RunStatus(return_code)
            result.end_time = datetime.now()
            process.result = result
        return process

    async def _wait_for(self, process: ExecutedProcess) -> CommandResult:
        try:
            await process.handle.wait()
            self.update_process(process)
            setup_script_path = self._setup_script_path(process.id.value)
            await self._connection.run(f"rm {shlex.quote(str(setup_script_path))}", check=True)
            process_dir = self._process_directory(process.id.value)
            await self._connection.run(f"rmdir {shlex.quote(str(process_dir))}", check=True)
        except TimeoutError as e:
            ExecutorException(f"Process {process.id.value} timed out:" +
                              str(process.command.command), e)
        except ProcessError as e:
            ExecutorException(f"Error during cleanup of {process.id.value}:" +
                              str(process.command.command), e)
        return process.result

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        return self._event_loop.run_until_complete(self._wait_for(process))

    def kill(self, process: ExecutedProcess):
        try:
            process.handle.kill()
            self.wait_for(process)
        except OSError as e:
            ExecutorException(f"Could not kill process ({process.command.command})", e)
