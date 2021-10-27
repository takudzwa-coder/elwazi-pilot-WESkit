#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import asyncio
from abc import abstractmethod, ABCMeta
from datetime import timedelta
from pathlib import PurePath

import pytest
import time
import yaml

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import ExecutionSettings, CommandResult, Executor
from weskit.classes.executor.LocalExecutor import LocalExecutor
from weskit.classes.executor.SshExecutor import SshExecutor
from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor
from weskit.memory_units import Memory, Unit

with open("tests/remote.yaml", "r") as f:
    remote_config = yaml.safe_load(f)


if remote_config is not None and "ssh" in remote_config.keys():
    ssh_executor = SshExecutor(**(remote_config["ssh"]))
else:
    ssh_executor = None


if remote_config is not None and "lsf_submission_host" in remote_config.keys():
    ssh_lsf_executor = LsfExecutor(SshExecutor(**(remote_config['lsf_submission_host']["ssh"])))
    remote_workdir = remote_config['lsf_submission_host']["remote_workdir"]
else:
    ssh_lsf_executor = None

# Note that this cannot be solved by a fixture yielding multiple times.
# See https://github.com/pytest-dev/pytest/issues/1595.
#
# Instead marks for individual parameters of pytest.mark.parametrize are used.
# See https://docs.pytest.org/en/6.2.x/example/markers.html#marking-individual-tests-when-using-parametrize   # noqa
#
# You can select the tests to execute on the commandline.
executors = {
    "local": pytest.param(LocalExecutor(),
                          marks=[pytest.mark.integration]),
    "ssh": pytest.param(ssh_executor,
                        marks=[pytest.mark.slow,
                               pytest.mark.integration,
                               pytest.mark.ssh]),
    "ssh_lsf": pytest.param(ssh_lsf_executor,
                            marks=[pytest.mark.slow,
                                   pytest.mark.integration,
                                   pytest.mark.ssh_lsf])
}


@pytest.mark.parametrize("executor", executors.values())
def test_submit_failing_command(executor):
    command = ShellCommand(["bash", "-c", "nonexistingcommand"],
                           workdir=PurePath("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_submit_failing_command",
                                   walltime=timedelta(minutes=5.0),
                                   total_memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    assert result.status.code == 127
    assert not result.status.success
    assert result.status.finished
    assert result.status.failed


@pytest.mark.parametrize("executor", executors.values())
def test_submit_nonexisting_command(executor):
    command = ShellCommand(["nonexistingcommand"],
                           workdir=PurePath("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_submit_nonexisting_command",
                                   walltime=timedelta(minutes=5.0),
                                   total_memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    assert result.status.code == 127


@pytest.mark.parametrize("executor", executors.values())
def test_inacessible_workdir(executor):
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=PurePath("/this/path/does/not/exist"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_inaccessible_workdir",
                                   walltime=timedelta(minutes=5.0),
                                   total_memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    # Note: LSF exits with code 2 with LSB_EXIT_IF_CWD_NOTEXIST=Y, but at least it fails.
    assert result.status.code in [1, 2], result.status


class ExecuteProcess(metaclass=ABCMeta):

    @property
    @abstractmethod
    def executor(self) -> Executor:
        pass

    @property
    @abstractmethod
    def workdir(self) -> PurePath:
        pass

    def execute(self, stdout_file, stderr_file) -> CommandResult:
        # Note: This tests exports ENV_VAL to Bash, as executed command. This variable (and $PWD)
        #       is then used to evaluate the shell expression.
        command = ShellCommand(["bash", "-c", "echo \"hello $ENV_VAL (from $PWD)\""],
                               workdir=self.workdir,
                               environment={
                                   "ENV_VAL": "world"
                               })
        process = self.executor.execute(command,
                                        stdout_file=stdout_file,
                                        stderr_file=stderr_file,
                                        settings=ExecutionSettings(
                                            job_name="weskit_test_execute",
                                            walltime=timedelta(minutes=5.0),
                                            total_memory=Memory(100, Unit.MEGA)))
        return self.executor.wait_for(process)

    def _assert_stdout(self, observed, expected):
        assert observed == expected

    def check_execution_result(self, result, remote_stdout_file, remote_stderr_file, stdout_file):
        assert result.status.code == 0
        assert result.stdout_file == remote_stdout_file
        assert result.stderr_file == remote_stderr_file

        with open(stdout_file, "r") as stdout:
            self._assert_stdout(stdout.readlines(), [f"hello world (from {str(self.workdir)})\n"])

        assert result.status.success
        assert result.status.finished
        assert not result.status.failed
        assert result.start_time is not None
        assert result.end_time is not None


@pytest.mark.integration
class TestExecuteLocalProcess(ExecuteProcess):

    @property
    def executor(self) -> LocalExecutor:
        return LocalExecutor()

    @property
    def workdir(self) -> PurePath:
        return self._workdir

    @workdir.setter
    def workdir(self, val: PurePath):
        self._workdir = val

    def test_execute(self, temporary_dir):
        self.workdir = PurePath(temporary_dir)
        stderr_file = self.workdir / "stderr"
        stdout_file = self.workdir / "stdout"

        result = self.execute(stdout_file, stderr_file)
        self.check_execution_result(result, stdout_file, stderr_file, stdout_file)


class ExecuteProcessViaSsh(ExecuteProcess):

    @property
    @abstractmethod
    def remote(self) -> str:
        pass

    @property
    @abstractmethod
    def copy_to_local(self, remote, local):
        pass

    def run_execute_test(self, temporary_dir):
        # We don't create a remote directory. Use /tmp as it is guaranteed to be present and
        # we don't have to care about cleanup.
        stderr_file = self.workdir / "stderr"
        stdout_file = self.workdir / "stdout"

        result = self.execute(stdout_file, stderr_file)

        local_temp = PurePath(temporary_dir)
        self.copy_to_local(stdout_file, local_temp / "stdout")

        self.check_execution_result(result, stdout_file, stderr_file, local_temp / "stdout")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ssh
class TestSubmitSshProcess(ExecuteProcessViaSsh):

    @property
    def executor(self) -> SshExecutor:
        return ssh_executor

    @property
    def remote(self) -> str:
        return self.executor.hostname

    @property
    def workdir(self) -> PurePath:
        return PurePath("/tmp")

    def copy_to_local(self, remote, local):
        asyncio.get_event_loop().run_until_complete(
            self.executor.copy_from_remote(remote, local))

    def test_execute(self, temporary_dir):
        self.run_execute_test(temporary_dir)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ssh_lsf
class TestSubmitLsfProcess(ExecuteProcessViaSsh):

    @property
    def executor(self) -> LsfExecutor:
        return ssh_lsf_executor

    @property
    def remote(self) -> str:
        return self.executor.executor.hostname

    @property
    def workdir(self) -> PurePath:
        return PurePath(remote_workdir)

    def copy_to_local(self, remote, local):
        asyncio.get_event_loop().run_until_complete(
            self.executor.executor.copy_from_remote(remote, local))

    def _assert_stdout(self, observed, expected):
        """
        LSF embeds the standard output into a file with lots of other information. We only want
        to check the standard output, whether the variables are correctly evaluated
        """
        # Ignore everything up to and including
        # "The output (if any) follows:"
        # ""
        #
        # Ignore everything the last 4 lines.
        indexed = next(filter(lambda l: l[1] == "The output (if any) follows:\n",
                              zip(range(0, len(observed) - 1), observed)),
                       None)
        print(indexed)
        if indexed is None:
            assert False, f"Invalid standard output: {observed}"
        fromIdx = indexed[0] + 2
        toIdx = len(observed) - 6
        print(observed[fromIdx:toIdx])
        assert observed[fromIdx:toIdx] == expected, f"Could not validate stdout: {observed}"

    def test_execute(self, temporary_dir):
        self.run_execute_test(temporary_dir)


# This tests an internal feature of the LocalExecutor().
@pytest.mark.parametrize("executor", [executors["local"]])
def test_std_fds_are_closed(executor, temporary_dir):
    workdir = PurePath(temporary_dir)
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=workdir)
    process = executor.execute(command,
                               stdout_file=workdir / "stdout",
                               stderr_file=workdir / "stderr")
    executor.wait_for(process)
    assert process.handle.stdout_fd.closed
    assert process.handle.stderr_fd.closed


@pytest.mark.parametrize("executor", executors.values())
def test_get_status(executor):
    command = ShellCommand(["sleep", "20" if isinstance(executor, LsfExecutor) else "1"],
                           workdir=PurePath("/"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_get_status",
                                   walltime=timedelta(minutes=5.0),
                                   total_memory=Memory(100, Unit.MEGA)))
    status = executor.get_status(process)
    assert status.code is None
    assert not status.finished
    assert not status.success
    assert not status.failed
    result = executor.wait_for(process)
    assert result.status.code == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed


@pytest.mark.parametrize("executor", [executors["local"], executors["ssh_lsf"]])
def test_update_process(executor):
    command = ShellCommand(["sleep", "20" if isinstance(executor, LsfExecutor) else "2"],
                           workdir=PurePath("/"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_update_process",
                                   walltime=timedelta(minutes=5.0),
                                   total_memory=Memory(100, Unit.MEGA)))
    executor.update_process(process)
    result = process.result
    assert result.status.code is None
    assert not result.status.finished
    assert not result.status.success
    assert not result.status.failed
    # The following test fails for the SSHExecutor, maybe because stream-flushing issues. If the
    # sleep is substituted by SshExecutor.wait_for() then in works.
    # executor.wait_for(process)
    time.sleep(5)
    executor.update_process(process)
    result = process.result
    assert result.status.code == 0
    assert result.status.success
    assert result.status.finished
    assert not result.status.failed


@pytest.mark.parametrize("executor", executors.values())
def test_kill_process(executor):
    # TODO Killing is not implemented yet.
    assert True
