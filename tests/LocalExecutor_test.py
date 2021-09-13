#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import time
from pathlib import PurePath

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.command_executor.LocalExecutor import LocalExecutor


def test_submit_local_process(temporary_dir):
    executor = LocalExecutor()
    command = ShellCommand(["bash", "-c", "echo -n \"hallo $ENV_VAL (from $PWD)\""],
                           workdir=PurePath("/"),
                           environment={
                               "ENV_VAL": "world"
                           })
    process = executor.submit(command,
                              stdout_file=PurePath(temporary_dir) / "stdout",
                              stderr_file=PurePath(temporary_dir) / "stderr")
    result = executor.wait_for(process)
    assert result.status.value == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed
    assert result.start_time is not None
    assert result.stdout_file == PurePath(temporary_dir) / "stdout"
    assert result.stderr_file == PurePath(temporary_dir) / "stderr"
    assert result.end_time is not None
    with open(PurePath(temporary_dir) / "stdout") as f:
        assert f.readlines() == ["hallo world (from /)"]


def test_submit_failing_command(temporary_dir):
    executor = LocalExecutor()
    command = ShellCommand(["bash", "-c", "nonexistingcommand"],
                           workdir=PurePath("/"))
    process = executor.submit(command,
                              stdout_file=PurePath(temporary_dir) / "stdout",
                              stderr_file=PurePath(temporary_dir) / "stderr")
    result = executor.wait_for(process)
    assert result.status.value == 127
    assert not result.status.success
    assert result.status.finished
    assert result.status.failed


def test_get_status(temporary_dir):
    executor = LocalExecutor()
    command = ShellCommand(["sleep", "1"],
                           workdir=PurePath("/"))
    process = executor.submit(command,
                              stdout_file=PurePath(temporary_dir) / "stdout",
                              stderr_file=PurePath(temporary_dir) / "stderr")
    status = executor.get_status(process)
    assert status.value is None
    assert not status.finished
    assert not status.success
    assert not status.failed
    result = executor.wait_for(process)
    assert result.status.value == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed


def test_update_process(temporary_dir):
    executor = LocalExecutor()
    command = ShellCommand(["sleep", "1"],
                           workdir=PurePath("/"))
    process = executor.submit(command,
                              stdout_file=PurePath(temporary_dir) / "stdout",
                              stderr_file=PurePath(temporary_dir) / "stderr")
    executor.update_process(process)
    result = process.result
    assert result.status.value is None
    assert not result.status.finished
    assert not result.status.success
    assert not result.status.failed
    time.sleep(1.1)
    executor.update_process(process)
    result = process.result
    assert result.status.value == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed


def test_std_fds_are_closed(temporary_dir):
    executor = LocalExecutor()
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=PurePath("/"))
    process = executor.submit(command,
                              stdout_file=PurePath(temporary_dir) / "stdout",
                              stderr_file=PurePath(temporary_dir) / "stderr")
    executor.wait_for(process)
    assert process.handle.stdout_fd.closed
    assert process.handle.stderr_fd.closed


def test_kill_process():
    # TODO Killing is not implemented yet.
    assert True
