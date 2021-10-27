#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from pathlib import PurePath

import pytest
import time
import yaml

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.executor.LocalExecutor import LocalExecutor
from weskit.classes.executor.SshExecutor import SshExecutor


def load_executors():
    execs = [LocalExecutor()]
    with open("tests/ssh.yaml", "r") as f:
        ssh_configs = yaml.safe_load(f)
    for config in ssh_configs["ssh"]:
        execs.append(SshExecutor(**config))
    return execs


# Note that this cannot be solved by a fixture yielding multiple times.
# See https://github.com/pytest-dev/pytest/issues/1595
executors = load_executors()


@pytest.mark.parametrize("executor", executors)
def test_submit_process(executor, temporary_dir):
    # Note: This tests exports ENV_VAL to Bash, as executed command. This variable (and $PWD)
    #       is then used to evaluate the shell expression.
    command = ShellCommand(["bash", "-c", "echo -n \"hello $ENV_VAL (from $PWD)\""],
                           workdir=PurePath("/"),
                           environment={
                               "ENV_VAL": "world"
                           })
    process = executor.execute(command,
                               stdout_file=PurePath(temporary_dir) / "stdout",
                               stderr_file=PurePath(temporary_dir) / "stderr")
    result = executor.wait_for(process)
    assert result.status.value == 0
    assert result.stdout_file == PurePath(temporary_dir) / "stdout"
    assert result.stderr_file == PurePath(temporary_dir) / "stderr"
    with open(result.stdout_file, "r") as f:
        assert f.readlines() == ["hello world (from /)"]
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed
    assert result.start_time is not None
    assert result.end_time is not None


@pytest.mark.parametrize("executor", executors)
def test_submit_failing_command(executor, temporary_dir):
    command = ShellCommand(["bash", "-c", "nonexistingcommand"],
                           workdir=PurePath("/"))
    process = executor.execute(command,
                               stdout_file=PurePath(temporary_dir) / "stdout",
                               stderr_file=PurePath(temporary_dir) / "stderr")
    result = executor.wait_for(process)
    assert result.status.value == 127
    assert not result.status.success
    assert result.status.finished
    assert result.status.failed


@pytest.mark.parametrize("executor", executors)
def test_submit_nonexisting_command(executor):
    command = ShellCommand(["nonexistingcommand"],
                           workdir=PurePath("/"))
    with pytest.raises(ExecutorException):
        executor.execute(command)


@pytest.mark.parametrize("executor", executors)
def test_inacessible_workdir(executor):
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=PurePath("/this/path/does/not/exist"))
    with pytest.raises(ExecutorException):
        executor.execute(command)


@pytest.mark.parametrize("executor", executors)
def test_get_status(executor, temporary_dir):
    command = ShellCommand(["sleep", "1"],
                           workdir=PurePath("/"))
    process = executor.execute(command,
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


# The following test fails for the SSHExecutor, maybe because stream-flushing issues. If the
# sleep is substituted by SSHexecutor.wait_for() then in works.
@pytest.mark.parametrize("executor", [LocalExecutor()])
def test_update_process(executor):
    command = ShellCommand(["sleep", "1"],
                           workdir=PurePath("/"))
    process = executor.execute(command)
    executor.update_process(process)
    result = process.result
    assert result.status.value is None
    assert not result.status.finished
    assert not result.status.success
    assert not result.status.failed
    # executor.wait_for(process)
    time.sleep(5)
    executor.update_process(process)
    result = process.result
    assert result.status.value == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed


# This tests an internal feature of the LocalExecutor().
@pytest.mark.parametrize("executor", [LocalExecutor()])
def test_std_fds_are_closed(executor, temporary_dir):
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=PurePath("/"))
    process = executor.execute(command,
                               stdout_file=PurePath(temporary_dir) / "stdout",
                               stderr_file=PurePath(temporary_dir) / "stderr")
    executor.wait_for(process)
    assert process.handle.stdout_fd.closed
    assert process.handle.stderr_fd.closed


@pytest.mark.parametrize("executor", executors)
def test_kill_process(executor):
    # TODO Killing is not implemented yet.
    assert True
