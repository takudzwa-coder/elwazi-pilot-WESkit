#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import json
import os.path
import shutil
from tempfile import mkdtemp

import pytest

from weskit.tasks.CommandTask import run_command


@pytest.fixture(scope="function")
def temporary_dir():
    tmpdir = mkdtemp(prefix=__name__)
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_run_command(temporary_dir):
    command = ["bash", "-c", "echo 'hello world' > x"]
    result = run_command(command=command, workdir=temporary_dir)
    assert result["output_files"] == ["x"]
    with open(os.path.join(temporary_dir, "x"), "r") as f:
        assert f.readlines() == ["hello world\n"]
    with open(result["command_file"], "r") as f:
        command_result = json.load(f)
        assert command_result["cmd"] == command
        assert command_result["exit_code"] == 0
        assert command_result["workdir"] == temporary_dir
        assert command_result["start_time"]
        assert command_result["end_time"]
    with open(result["stderr_file"], "r") as f:
        assert len(f.readlines()) == 0
    with open(result["stdout_file"], "r") as f:
        assert len(f.readlines()) == 0
