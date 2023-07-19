# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from contextlib import contextmanager, asynccontextmanager
from os import unlink, rmdir, walk, makedirs
from pathlib import Path
from shutil import copytree, copy2, rmtree
from typing import List, Iterator, IO

from urllib3.util import Url

from weskit.classes.storage.StorageAccessor import StorageAccessor


class LocalStorageAccessor(StorageAccessor):

    def __init__(self):
        pass

    async def copy(self,
                   source: Path,
                   target: Path,
                   recurse: bool = False,
                   dirs_exist_ok: bool = False) -> None:
        if source == target:
            pass
        else:
            if not dirs_exist_ok and target.exists():
                raise FileExistsError(f"Destination '{target}' exists and dirs_exist_ok=False")
            elif recurse:
                copytree(source, target,
                         dirs_exist_ok=dirs_exist_ok,
                         copy_function=copy2)
            else:
                copy2(source, target, follow_symlinks=False)

    async def put(self,
                  source: Path,
                  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        This is just a copy operation for this `LocalExecutor`. If the files are identical,
        then simply ignore the operation.
        """
        await self.copy(source, target, recurse, dirs_exist_ok)

    async def get(self,
                  source: Path,
                  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        For the `LocalExecutor` putting and getting are the same.
        """
        await self.copy(source, target, recurse, dirs_exist_ok)

    async def remove_file(self, target: Path) -> None:
        unlink(target)

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        await super(LocalStorageAccessor, self).remove_dir(target, recurse)
        if recurse:
            if rmtree.avoids_symlink_attacks:   # type: ignore[attr-defined]
                rmtree(target)
            else:
                raise NotImplementedError()
        else:
            rmdir(target)

    async def find(self, target: Path) -> List[Path]:
        results: List[Path] = []
        for root, dirs, files in walk(target):
            root_p = Path(root)
            results += [root_p / file for file in files]
        return results

    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
        makedirs(target, mode=mode, exist_ok=exists_ok)

    @asynccontextmanager
    async def open(self,
                   url: Url,
                   *args,
                   **kwargs) \
            -> Iterator[IO[str]]:
        if url.scheme is None or url.scheme == "file":
            file = url.path
            with open(file=file, *args, **kwargs) as fh:
                yield fh
        else:
            raise ValueError(f"Can only use file:// URLs: '{url}'")
