# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import shlex
from pathlib import Path
from typing import List

import asyncssh

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
