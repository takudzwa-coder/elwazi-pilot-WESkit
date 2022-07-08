#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import json
import os.path
from pathlib import Path

import pytest

import Executor_test
from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.CommandTask import run_command


def test_run_command(temporary_dir, test_config):
    command = ["echo", "hello world", ss(">"), "x"]
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir))
    workdir = Path(temporary_dir)
    command_obj = ShellCommand(command=command,
                               workdir=workdir)
    result = run_command(command=command_obj,
                         worker_context=context,
                         executor_context=context,
                         executor_config=test_config['executor'],
                         execution_settings=ExecutionSettings())
    with open(os.path.join(temporary_dir, result["log_file"]), "r") as f:
        command_result = json.load(f)
        assert command_result["workdir"] == str(workdir)
        assert command_result["cmd"] == [str(el) for el in command]
        assert command_result["exit_code"] == 0
        assert command_result["start_time"]
        assert command_result["end_time"]
    assert result["output_files"] == ["x"]
    with open(os.path.join(temporary_dir, "x"), "r") as f:
        assert f.readlines() == ["hello world\n"]
    with open(os.path.join(temporary_dir, result["stderr_file"]), "r") as f:
        assert len(f.readlines()) == 0
    with open(os.path.join(temporary_dir, result["stdout_file"]), "r") as f:
        assert len(f.readlines()) == 0


@pytest.mark.ssh
def test_run_command_ssh(temporary_dir, test_config):
    command = ["echo", "hello world", ss(">"), "x"]
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir))
    workdir = Path(temporary_dir)
    command_obj = ShellCommand(command=command,
                               workdir=workdir,
                               environment={})
    result = run_command(command=command_obj,
                         worker_context=context,
                         executor_context=context,
                         execution_settings=ExecutionSettings(),
                         executor_config={
                            "type": "ssh",
                            "remote_data_dir": "/tmp",
                            "remote_workflows_dir": "/tmp",
                            "login": Executor_test.remote_config["ssh"]  # "ssh" in remote.yaml
                         })
    with open(os.path.join(temporary_dir, result["log_file"]), "r") as f:
        command_result = json.load(f)
        assert command_result["workdir"] == str(workdir)
        assert command_result["cmd"] == [str(el) for el in command]
        assert command_result["exit_code"] == 0
        assert command_result["start_time"]
        assert command_result["end_time"]
    assert result["output_files"] == ["x"]
    with open(os.path.join(temporary_dir, "x"), "r") as f:
        assert f.readlines() == ["hello world\n"]
    with open(os.path.join(temporary_dir, result["stderr_file"]), "r") as f:
        assert len(f.readlines()) == 0
    with open(os.path.join(temporary_dir, result["stdout_file"]), "r") as f:
        assert len(f.readlines()) == 0
