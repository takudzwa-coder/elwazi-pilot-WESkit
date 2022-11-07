#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from abc import abstractmethod, ABCMeta
from pathlib import Path
from typing import List


class StorageAccessor(metaclass=ABCMeta):

    # The following methods are used to communicate files between the storage infrastructure used
    # for the execution and the local storage.

    @abstractmethod
    async def put(self, source: Path,  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        Copy a file associated with the execution of a job from source to target. Implicitly the
        target is remote, if the executor is a remote executor then the copying is associated
        with a network transfer. It is tried to copy the permission bits and modification times.
        """
        pass

    @abstractmethod
    async def get(self, source: Path,  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        Copy a file associated with the execution of a job from source to target. Implicitly the
        source is remote, if the executor is a remote executor then the copying is associated
        with a network transfer. It is tried to copy the permission bits and modification times.
        """
        pass

    @abstractmethod
    async def remove_file(self, target: Path) -> None:
        """
        Remove the target file. If the executor is a remote executor, then the target is removed
        remotely. As a safety measure only absolute paths are allowed as targets.
        """
        if not target.is_absolute():
            raise ValueError(f"Will only delete absolute paths! Refusing to delete '{target}'")

    @abstractmethod
    async def create_dir(self, target: Path, exists_ok=False, **kwargs) -> None:
        """
        Create the target directory. If the executor is a remote executor, then the target is
        created remotely.
        """
        pass

    @abstractmethod
    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        """
        Remove target directory. If the executor is a remote executor, then the target is removed
        remotely. As a safety measure only absolute paths are allowed as targets.
        """
        if not target.is_absolute():
            raise ValueError(f"Will only delete absolute paths! Refusing to delete '{target}'")

    @abstractmethod
    async def find_files(self, target: Path) -> List[Path]:
        """
        Return the files located in the target path (remote for a remote executor). The paths are
        relative to the target path.
        """
        pass
