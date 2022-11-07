#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from os import unlink, rmdir, walk, makedirs
from pathlib import Path
from shutil import copytree, copy2, rmtree
from typing import List

from weskit.classes.executor.StorageAccessor import StorageAccessor


class LocalStorageAccessor(StorageAccessor):

    def __init__(self):
        pass

    async def put(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        This is just a copy operation for this `LocalExecutor`. If the files are identical,
        then simply ignore the operation.
        """
        if source == target:
            pass
        elif recurse:
            copytree(source, target,
                     dirs_exist_ok=dirs_exist_ok,
                     copy_function=copy2)
        else:
            copy2(source, target, follow_symlinks=False)

    async def get(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        For the `LocalExecutor` putting and getting are the same.
        """
        if source == target:
            pass
        elif recurse:
            copytree(source, target,
                     dirs_exist_ok=dirs_exist_ok,
                     copy_function=copy2)
        else:
            copy2(source, target, follow_symlinks=False)

    async def remove_file(self, target: Path) -> None:
        await super(LocalStorageAccessor, self).remove_file(target)
        unlink(target)

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        await super(LocalStorageAccessor, self).remove_dir(target, recurse)
        if recurse:
            rmtree(target)
        else:
            rmdir(target)

    async def find_files(self, target: Path) -> List[Path]:
        results: List[Path] = []
        for root, dirs, files in walk(target):
            root_p = Path(root)
            results += [root_p / file for file in files]
        return results

    async def create_dir(self, target: Path, **kwargs) -> None:
        makedirs(target, **kwargs)
