# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import shlex
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Iterator, IO

import asyncssh
from urllib3.util import Url

from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.storage.StorageAccessor import StorageAccessor


class SshStorageAccessor(StorageAccessor):

    def __init__(self, connection: RetryableSshConnection):
        self._connection = connection

    async def _file_exists(self, path: Path) -> bool:
        async with self._connection.context():
            proc = await self._connection.run("test -f %s" % shlex.quote(str(path)))
            return proc.exit_status == 0

    async def _dir_exists(self, path: Path) -> bool:
        async with self._connection.context():
            proc = await self._connection.run("test -d %s" % shlex.quote(str(path)))
            return proc.exit_status == 0

    async def put(self,
                  source: Path,
                  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False,
                  **kwargs) -> None:
        async with self._connection.context():
            target_is_existing_dir = await self._dir_exists(target)
            real_target = target
            if target_is_existing_dir:
                if not dirs_exist_ok:
                    raise FileExistsError("Destination '%s' exists on %s and dirs_exist_ok=False" %
                                          (str(target), self._connection.host_url))
                else:
                    real_target = target / source.name

            await asyncssh.scp(srcpaths=str(source),
                               dstpath=(self._connection.raw, str(real_target)),
                               preserve=True,
                               recurse=recurse,
                               **kwargs)

    async def get(self,
                  source: Path,
                  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False,
                  **kwargs) -> None:
        if not dirs_exist_ok and target.exists():
            raise FileExistsError(f"Destination '{target}' exists and dirs_exist_ok=False")
        async with self._connection.context():
            await asyncssh.scp(srcpaths=(self._connection.raw, str(source)),
                               dstpath=str(target),
                               preserve=True,
                               recurse=recurse,
                               **kwargs)

    async def remove_file(self, target: Path) -> None:
        exists = await self._file_exists(target)
        async with self._connection.context():
            if not exists:
                raise FileNotFoundError(target)
            await self._connection.run(f"rm {shlex.quote(str(target))}",
                                       check=True)

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        await super(SshStorageAccessor, self).remove_dir(target, recurse)
        exists = await self._dir_exists(target)
        if not exists:
            raise OSError(f"Cannot remove '{target}' because it does not exist")
        async with self._connection.context():
            if recurse:
                await self._connection.run(f"rm -r {shlex.quote(str(target))}",
                                           check=True)
            else:
                if len(await self.find(target)) != 0:
                    raise OSError(f"Directory not empty: '{target}'")
                await self._connection.run(f"rmdir {shlex.quote(str(target))}",
                                           check=True)

    async def find(self, target: Path) -> List[Path]:
        async with self._connection.context():
            completed_process = \
                await self._connection.run(f"find {shlex.quote(str(target))}",
                                           check=True)
            if completed_process.returncode == 0:
                if completed_process.stdout is not None and len(completed_process.stdout) > 0:
                    return [Path(path)
                            for path in str(completed_process.stdout).split("\n")
                            if path != "" and path != str(target)]
                else:
                    return []
            else:
                raise RuntimeError("Oops! Shouldn't happen because of check=True")

    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
        async with self._connection.context():
            await self._connection.run("set -ue; umask %04o; mkdir %s %s" %
                                       (
                                           mode,
                                           "-p" if exists_ok else "",
                                           shlex.quote(str(target))
                                       ),
                                       check=True)

    @asynccontextmanager
    async def open(self,
                   url: Url,
                   mode: str = "rt",
                   block_size: int = 16384,
                   encoding: str = "UTF-8",
                   *args,
                   **kwargs) \
            -> Iterator[IO[str]]:
        """
        This buffers the remote file locally. In write mode, the local temporary file is copied
        back to the server, after the block is left. Note that in write-mode, if the with-block
        ends with an exception, the possibly broken result file anyway is uploaded to the server!
        This is to mimic the behaviour of a local IO operation as much as possible.

        Still, this differs in terms of file access from os.open(), in that the writing operations
        do not modify an existing file, but create a new directory entry for a file with the same
        name as a possibly existing file. Concurrent remote processes will not be affected in the
        same way as local processes are by os.open().

        The `url` scheme must be undefined, `file`, or `ssh`. For undefined and `file` it is
        assumed that the file is on the server side. If the `url` has a host set, then the
        host must match the hostname of the connection.
        """
        def is_write(mode: str) -> bool:
            return len(set(mode.split()).intersection({"w", "x", "a"})) > 0

        def is_truncating_write(mode: str) -> bool:
            return "+" in mode

        def is_exclusive_creation(mode: str) -> bool:
            return "x" in mode

        if url.scheme is None or url.scheme == "file" or url.scheme == "ssh" \
                and (url.hostname is None or url.hostname == self._connection.hostname):
            file = Path(url.path)

            if not is_write(mode):
                with NamedTemporaryFile(encoding=encoding, mode=mode) as local:
                    # Try to copy the file from remote. This fails, if the file does not exist.
                    await asyncssh.scp((self._connection, file), local.name, block_size=block_size)
                    # We have to re-open the file, because the copy operation
                    # overwrite the original temporary file.
                    with open(local.name, mode=mode, encoding=encoding,
                              *args, **kwargs) as fh:
                        yield fh

            else:  # is_write(mode)
                try:
                    with NamedTemporaryFile(encoding=encoding, mode=mode) as local:
                        if is_exclusive_creation(mode):
                            proc = await self._connection.run(["bash", "-c",
                                                              f"[ -f {shlex.quote(str(file))} ]"])
                            if proc.exit_status == 0:
                                raise FileExistsError(f"File exists on {self._connection.hostname}: "
                                                      f"{url}")
                            else:
                                # Create a new local file.
                                yield local
                        else:  # not is_exclusive_creation(mode)
                            if is_truncating_write(mode):
                                yield local
                            else:  # not is_truncating_write(mode)
                                try:
                                    # Copy the remote file, if it exists.
                                    await asyncssh.scp((self._connection.raw, file),
                                                       local.name,
                                                       block_size=block_size)
                                except ...:
                                    # If the file does not exist, fine. Just create a local file.
                                    # TODO: Which error to catch, if remote file does not exist?
                                with open(local.name, mode=mode, encoding=encoding,
                                          *args, **kwargs) as fh:
                                    # We have to re-open the file, because the copy operation
                                    # overwrite the original temporary file.
                                    yield fh
                finally:
                    # Copy back the result, if the file was opened in any write-mode.
                    await asyncssh.scp(local.name,
                                       (self._connection.raw, file),
                                       block_size=block_size)
        else:
            raise ValueError(f"Can only use file:// or ssh:// URLs: '{url}'")
