# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import json
import os.path
import tempfile
from pathlib import Path

import pytest
import yaml

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
def test_run_command_ssh(temporary_dir, test_config, remote_config):
    with tempfile.NamedTemporaryFile("w", prefix="config", suffix=".yaml") as config_file:
        config = {
            "executor": {
                "type": "ssh",
                "remote_data_dir": "/tmp",
                "remote_workflows_dir": "/tmp",
                "login": remote_config["ssh"]  # "ssh" in remote.yaml
            }
        }
        original_config = os.getenv("WESKIT_CONFIG")

        try:
            print(yaml.dump(config), file=config_file)
            os.environ["WESKIT_CONFIG"] = config_file.name

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
                                 execution_settings=ExecutionSettings())
            with open(os.path.join(temporary_dir, result["log_file"]), "r") as f:
                command_result = json.load(f)
                assert command_result["workdir"] == str(workdir)
                assert command_result["cmd"] == [str(el) for el in command]
                assert command_result["exit_code"] == 0
                assert command_result["start_time"]
                assert command_result["end_time"]
                assert command_result["stdout_file"].startswith(".weskit")
                assert command_result["stderr_file"].startswith(".weskit")
                assert command_result["log_dir"].startswith(".weskit")
                assert command_result["log_file"].startswith(".weskit")
            assert result["output_files"] == ["x"]
            with open(os.path.join(temporary_dir, "x"), "r") as f:
                assert f.readlines() == ["hello world\n"]
            with open(os.path.join(temporary_dir, result["stderr_file"]), "r") as f:
                assert len(f.readlines()) == 0
            with open(os.path.join(temporary_dir, result["stdout_file"]), "r") as f:
                assert len(f.readlines()) == 0
        finally:
            os.environ["WESKIT_CONFIG"] = original_config
