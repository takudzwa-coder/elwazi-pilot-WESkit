#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import shlex
from pathlib import Path
from typing import List

import asyncssh

from weskit.classes.executor.unix.RetryableSshConnection import RetryableSshConnection
from weskit.classes.executor.StorageAccessor import StorageAccessor


class SshStorageAccessor(StorageAccessor):

    def __init__(self, connection: RetryableSshConnection):
        self._connection = connection

    async def _dir_exists(self, path: Path) -> bool:
        async  with self._connection.context():
            proc = await self._connection.run("test -d %s" % shlex.quote(str(path)))
            return proc.exit_status != 0

    async def put(self, srcpath: Path, dstpath: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False,
                  **kwargs) -> None:
        async with self._connection.context():
            if not dirs_exist_ok and await self._dir_exists(dstpath):
                raise FileExistsError(f"Destination '%s' exists on %s and dirs_exist_ok=False" %
                                      str(dstpath),
                                      self._connection.host_url)
            await asyncssh.scp(srcpaths=str(srcpath),
                               dstpath=(self._connection.raw, str(dstpath)),
                               preserve=True,
                               recurse=recurse,
                               **kwargs)

    async def get(self, srcpath: Path, dstpath: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False,
                  **kwargs) -> None:
        if not dirs_exist_ok and dstpath.exists():
            raise FileExistsError(f"Destination '{dstpath}' exists and dirs_exist_ok=False")
        async with self._connection.context():
            await asyncssh.scp(srcpaths=(self._connection.raw, str(srcpath)),
                               dstpath=str(dstpath),
                               preserve=True,
                               recurse=recurse,
                               **kwargs)

    async def remove_file(self, target: Path) -> None:
        await super(SshStorageAccessor, self).remove_file(target)
        async with self._connection.context():
            await self._connection.run(f"rm {shlex.quote(str(target))}",
                                       check=True)

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        await super(SshStorageAccessor, self).remove_dir(target, recurse)
        async with self._connection.context():
            if recurse:
                await self._connection.run(f"rm -r {shlex.quote(str(target))}",
                                           check=True)
            else:
                await self._connection.run(f"rmdir {shlex.quote(str(target))}",
                                           check=True)

    async def find_files(self, target: Path) -> List[Path]:
        async with self._connection.context():
            completed_process = \
                await self._connection.run(f"find {shlex.quote(str(target))} -type f",
                                           check=True,
                                           encodings="UTF-8")
            if completed_process.returncode == 0:
                return [Path(path) for path in str(completed_process.stdout).split("\n")]
            else:
                raise RuntimeError("Oops! Shouldn't happen because of check=True")

    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
        async with self._connection.context():
            await self._connection.run("set -ue; umask %04o; mkdir %s %s}" %
                                       (
                                           mode,
                                           "-p" if exists_ok else "",
                                           shlex.quote(str(target))
                                       ),
                                       check=True)
