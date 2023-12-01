# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from abc import abstractmethod, ABCMeta
from pathlib import Path
from typing import List


class StorageAccessor(metaclass=ABCMeta):

    # The following methods are used to communicate files between the storage infrastructure used
    # for the execution and the local storage.

    @abstractmethod
    async def put(self,
                  source: Path,
                  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        Copy a file associated with the execution of a job from source to target. If the executor
        is a remote executor then implicitly the target is remote  then the copying is associated
        with a network transfer. It is tried to copy the permission bits and modification times.

        If `target` specifies a directory, the source will be copied into target using the base
        filename from source. If `target` specifies a file that already exists, it will be replaced.

        If `dirs_exist_ok` is `True`, ignore whether the target path exists. Otherwise, fail with a
        `FileExistsError`. Note that this check only applies to the top-level directory if the
        source is a directory and `recurse=True`.
        """
        pass

    @abstractmethod
    async def get(self, source: Path,  target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        """
        Like put, only the other way around.
        """
        pass

    @abstractmethod
    async def remove_file(self, target: Path) -> None:
        """
        Remove the target file. If the executor is a remote executor, then the target is removed
        remotely.
        """
        pass

    @abstractmethod
    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
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

        If the target does not exist, an OSError is raised.

        If the target directory is not empty, but recurse is False, an OSError is raised.
        """
        if not target.is_absolute():
            raise ValueError(f"Will only delete absolute paths! Refusing to delete '{target}'")

    @abstractmethod
    async def find(self, target: Path) -> List[Path]:
        """
        Return the files and subdirectories located in the target path (remote for a remote
        executor). The paths are relative to the target path. The target path itself is not
        returned.
        """
        pass


# The MockStorageAccessor wont be tested now because it is not used in the Executor class
class MockStorageAccessor(StorageAccessor):

    async def put(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        print(f"Copying {source} to {target}")

    async def get(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        print(f"Copying {source} from {target}")

    async def remove_file(self, target: Path) -> None:
        print(f"Removing file at {target}")

    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
        print(f"Creating directory at {target}")

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        print(f"Removing directory at {target}")

    async def find(self, target: Path) -> List[Path]:
        print(f"Finding files and subdirectories at {target}")
        return [Path("file1.txt"), Path("file2.txt"), Path("subdir")]
