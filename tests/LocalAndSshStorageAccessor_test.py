# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile

import pytest

from weskit.classes.storage.LocalStorageAccessor import LocalStorageAccessor
from weskit.classes.storage.SshStorageAccessor import SshStorageAccessor


@pytest.fixture(scope="session")
def local_accessor():
    return LocalStorageAccessor()


@pytest.fixture(scope="session")
def ssh_accessor(ssh_local_connection, event_loop):
    return SshStorageAccessor(ssh_local_connection)


accessor_names = [pytest.param("local_accessor"),
                  pytest.param("ssh_accessor", marks=[
                      pytest.mark.ssh
                  ])]


@pytest.mark.asyncio
@pytest.mark.parametrize("accessor_name", accessor_names)
async def test_put_and_get(accessor_name, request):
    accessor = request.getfixturevalue(accessor_name)
    for fun in [accessor.put, accessor.get]:
        # These should have the same behaviour for the LocalStorageAccessor and the
        # SshStorageAccessor logging in to "localhost".

        with TemporaryDirectory() as a:
            with TemporaryDirectory() as b:
                # non-recursive
                from1 = Path(a) / "test1"
                to1 = Path(b) / "test1"
                with open(from1, "w") as af:
                    print("hello", file=af)
                await fun(from1, to1, recurse=False, dirs_exist_ok=True)
                assert to1.exists()

                # recursive
                from2 = Path(a) / "test2"
                to2 = Path(b) / "test2"
                os.mkdir(from2)
                os.mkdir(from2 / "within1")
                await fun(from2, to2, recurse=True, dirs_exist_ok=True)

                assert to2.exists() and (to2 / "within1").exists()

                with pytest.raises(FileExistsError):
                    await fun(from2, to2, recurse=True)

                os.mkdir(from2 / "within2")
                await fun(from2, to2 / "within2", recurse=True, dirs_exist_ok=True)
                assert (to2 / "within2").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("accessor_name", accessor_names)
async def test_remove_file(accessor_name, request):
    accessor = request.getfixturevalue(accessor_name)
    with NamedTemporaryFile(delete=False) as f:
        path = Path(f.name)

        await accessor.remove_file(path)

        assert not path.exists()
        with pytest.raises(FileNotFoundError):
            await accessor.remove_file(path)

    with TemporaryDirectory(ignore_cleanup_errors=True) as path:
        with pytest.raises(OSError):
            await accessor.remove_file(Path(path))


@pytest.mark.asyncio
@pytest.mark.parametrize("accessor_name", accessor_names)
async def test_create_dir(accessor_name, request):
    accessor = request.getfixturevalue(accessor_name)
    with TemporaryDirectory() as base:
        base_p = Path(base)
        await accessor.create_dir(base_p / "test")
        assert (base_p / "test").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("accessor_name", accessor_names)
async def test_remove_dir(accessor_name, request):
    accessor = request.getfixturevalue(accessor_name)
    with TemporaryDirectory() as base:
        test1 = Path(base) / "test1"
        os.mkdir(test1)
        await accessor.remove_dir(test1)
        assert not test1.exists()

        test2 = Path(base) / "test2"
        os.mkdir(test2)
        os.mkdir(test2 / "inner")
        with pytest.raises(OSError):
            await accessor.remove_dir(test2, recurse=False)

        await accessor.remove_dir(test2, recurse=True)
        assert not test2.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("accessor_name", accessor_names)
async def test_find_files(accessor_name, request):
    accessor = request.getfixturevalue(accessor_name)
    with TemporaryDirectory() as base:
        base_p = Path(base)

        assert await accessor.find(base_p) == []

        os.system("touch '%s'" % str(base_p / "test1"))
        os.system("touch '%s'" % str(base_p / "test2"))

        assert set(await accessor.find(base_p)) == {base_p / "test1", base_p / "test2"}
