# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Sequence, Optional

import asyncssh
from asyncssh import SSHKey, SSHClientConnection, SSHCompletedProcess, SSHClientProcess
from tenacity import \
    AsyncRetrying, retry_if_exception, stop_after_attempt, wait_random, wait_exponential, after_log
from urllib3.util import Url

from weskit.classes.executor.ExecutorError import ExecutorError, ConnectionError

logger = logging.getLogger(__name__)


def is_connection_interrupted(exception: BaseException) -> bool:
    return isinstance(exception, asyncssh.ChannelOpenError) and \
           exception.reason in ["SSH connection closed", "SSH connection lost"]


class RetryableSshConnection:
    """
    Just a thin convenience-wrapper around asyncssh and tenacity.
    """

    def __init__(self,
                 username: str,
                 hostname: str,
                 keyfile: Path,
                 keyfile_passphrase: str,
                 knownhosts_file: Path,
                 connection_timeout: str = "2m",
                 keepalive_interval: str = "30s",
                 keepalive_count_max: int = 5,
                 port: int = 22,
                 retry_options: Optional[dict] = None):
        """
        Keepalive: This is for a server application. The default is to have a keep-alive, but one
                   that allows recovery after even a long downtime of the remote host.

        :param username: Remote SSH username.
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
        self._connection_timeout = connection_timeout
        self._keepalive_interval = keepalive_interval
        self._keepalive_count_max = keepalive_count_max
        self._keyfile = keyfile
        self._keyfile_passphrase = keyfile_passphrase
        self._port = port
        self._knownhosts_file = knownhosts_file

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

        self._connection: Optional[SSHClientConnection] = None

    async def connect(self) -> None:
        # Some related docs:
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-known-hosts
        # * https://asyncssh.readthedocs.io/en/latest/api.html#specifying-private-keys
        # * https://asyncssh.readthedocs.io/en/latest/api.html#sshclientconnectionoptions
        ssh_keys: Sequence[SSHKey] = asyncssh.read_private_key_list(Path(self._keyfile),
                                                                    self._keyfile_passphrase)
        logger.info(f"Read private keys from {self._keyfile}. " +
                    f"sha256 fingerprints: {list(map(lambda k: k.get_fingerprint(), ssh_keys))}")
        try:
            self._connection = \
                await asyncssh.connect(host=self.hostname,
                                       port=self.port,
                                       username=self.username,
                                       client_keys=ssh_keys,
                                       known_hosts=str(self._knownhosts_file),
                                       login_timeout=self._connection_timeout,
                                       keepalive_interval=self._keepalive_interval,
                                       keepalive_count_max=self._keepalive_count_max,
                                       # By default, do not forward the local environment.
                                       env={},
                                       send_env={})
            logger.debug(f"Connected to {self._remote_name}")
        except asyncssh.DisconnectError as e:
            raise ExecutorError("Connection error (disconnect)", e)
        except asyncio.TimeoutError as e:
            raise ExecutorError("Connection error (timeout)", e)

    def disconnect(self) -> None:
        if self._connection is not None:
            self._connection.disconnect(code=11,   # SSH_DISCONNECT_BY_APPLICATION
                                        reason="Disconnection by request of WESkit")

    async def reconnect(self):
        try:
            await self.run('echo "Connection is active"')
            logger.info("Connection is active")
        except asyncssh.Error:
            logger.info("Connection is closed")
            logger.info("Reconnecting...")
            await self.connect()

    @property
    def raw(self) -> SSHClientConnection:
        if self._connection is None:
            raise RuntimeError("RetryableSshConnection.connect() was never called!")
        else:
            return self._connection

    def _reconnection_retry_options(self, **kwargs) -> dict:
        """
        All retries should wrap around external asynchronous calls, such as asyncssh, or
        async functions that themselves do no retry, because errors are simply re-raised.
        Thus, if the same error is causing a retry at multiple levels, retry attempts multiply!
        """
        return {**self._retry_options,
                "reraise": True,
                "retry": retry_if_exception(is_connection_interrupted),
                "after": after_log(logger, logging.DEBUG),
                **kwargs}

    @asynccontextmanager
    async def context(self, **kwargs):
        """
        A context manager that simplifies the calling of SSH operations with retry. You can add
        parameters to tenacity.AsyncRetrying to override any defaults.

        with self._retryable_connection():
            do_ssh_op()

        Exceptions raised by asyncssh are wrapped in an ExecutorError.
        """
        try:
            async for attempt in AsyncRetrying(before=await self.reconnect(),
                                               **self._reconnection_retry_options(**kwargs)):
                with attempt:
                    yield self
        except asyncssh.DisconnectError as e:
            raise ConnectionError("Disconnected", e)
        except asyncssh.ChannelOpenError as ex:
            raise ConnectionError("Channel open failed", ex)
        except asyncssh.Error as ex:
            raise ExecutorError("SSH error", ex)

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
    def keyfile(self) -> Path:
        return self._keyfile

    @property
    def _remote_name(self) -> str:
        return f"{self.username}@{self.hostname}:{self.port}"

    @property
    def host_url(self) -> Url:
        """
        Return the host to which an SSH connection is established to execute a command.

        * https://datatracker.ietf.org/doc/id/draft-salowey-secsh-uri-00.html
        * https://www.rfc-editor.org/rfc/rfc3986
        """
        return Url(scheme="ssh",
                   auth=self._username,
                   host=self._hostname,
                   port=self._port)

    async def run(self, *args, **kwargs) -> SSHCompletedProcess:
        if self._connection is None:
            raise RuntimeError("RetryableSshConnection not initialized")
        else:
            return await self._connection.run(*args, **kwargs)

    async def create_process(self, *args, **kwargs) -> SSHClientProcess:
        if self._connection is None:
            raise RuntimeError("RetryableSshConnection not initialized")
        else:
            return await self._connection.create_process(*args, **kwargs)
