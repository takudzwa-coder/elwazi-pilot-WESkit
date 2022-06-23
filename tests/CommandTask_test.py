#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import json
import os.path
from datetime import datetime
from pathlib import Path

import pytest

import Executor_test
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.CommandTask import PathContext
from weskit.tasks.CommandTask import run_command
from weskit.utils import format_timestamp


def test_path_context():
    timestamp = datetime.now()
    base = Path("base")
    sub = Path("sub")
    logs = Path("logs")
    context = PathContext(base,
                          sub,
                          timestamp,
                          logs)
    assert context.run_subdir == sub
    assert context.run_dir == base / sub
    assert context.workdir == context.run_dir
    assert context.log_base_subdir == logs
    assert context.timestamp == timestamp
    assert context.log_dir == base / sub / logs / format_timestamp(timestamp)
    assert context.stderr_file == context.log_dir / "stderr"
    assert context.stdout_file == context.log_dir / "stdout"
    assert context.execution_log_file == context.log_dir / "log.json"


def test_path_context_relocate():
    timestamp = datetime.now()
    base = Path("base")
    sub = Path("sub")
    logs = Path("logs")
    context = PathContext(base,
                          sub,
                          timestamp,
                          logs)

    new_base = Path("new_base")
    relocated = context.relocate(new_base)

    assert relocated.workdir == new_base / sub
    assert relocated.log_dir == new_base / sub / logs / format_timestamp(timestamp)


def test_run_command(temporary_dir, test_config):
    command = ["bash", "-c", "echo 'hello world' > x"]
    data_dir = Path(temporary_dir).parent
    workdir = Path(temporary_dir).name
    result = run_command(command=command,
                         local_base_workdir=str(data_dir),
                         sub_workdir=workdir,
                         executor_parameters=test_config['executor'],
                         execution_settings=ExecutionSettings())
    assert result["output_files"] == ["x"]
    with open(os.path.join(temporary_dir, "x"), "r") as f:
        assert f.readlines() == ["hello world\n"]
    with open(os.path.join(temporary_dir, result["log_file"]), "r") as f:
        command_result = json.load(f)
        assert command_result["workdir"] == workdir
        assert command_result["cmd"] == command
        assert command_result["exit_code"] == 0
        assert command_result["start_time"]
        assert command_result["end_time"]
    with open(os.path.join(temporary_dir, result["stderr_file"]), "r") as f:
        assert len(f.readlines()) == 0
    with open(os.path.join(temporary_dir, result["stdout_file"]), "r") as f:
        assert len(f.readlines()) == 0


@pytest.mark.ssh
def test_run_command_ssh(temporary_dir, test_config):
    command = ["bash", "-c", "echo 'hello world' > x"]
    data_dir = Path(temporary_dir).parent
    workdir = Path(temporary_dir).name
    result = run_command(command=command,
                         local_base_workdir=str(data_dir),
                         sub_workdir=workdir,
                         execution_settings=ExecutionSettings(),
                         executor_parameters={
                            "type": "ssh",
                            "remote_base_dir": "/tmp",
                            "login": Executor_test.remote_config["ssh"]  # "ssh" in remote.yaml
                         })
    assert result["output_files"] == ["x"]
    with open(os.path.join(temporary_dir, "x"), "r") as f:
        assert f.readlines() == ["hello world\n"]
    with open(os.path.join(temporary_dir, result["log_file"]), "r") as f:
        command_result = json.load(f)
        assert command_result["workdir"] == workdir
        assert command_result["cmd"] == command
        assert command_result["exit_code"] == 0
        assert command_result["start_time"]
        assert command_result["end_time"]
    with open(os.path.join(temporary_dir, result["stderr_file"]), "r") as f:
        assert len(f.readlines()) == 0
    with open(os.path.join(temporary_dir, result["stdout_file"]), "r") as f:
        assert len(f.readlines()) == 0
