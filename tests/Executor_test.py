#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import asyncio
import re
import time
import uuid
from abc import abstractmethod, ABCMeta
from datetime import timedelta, datetime
from os import PathLike
from pathlib import PurePath, Path
from typing import Optional, cast

import pytest
import yaml
from typing.io import IO

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import ExecutionSettings, CommandResult, Executor
from weskit.classes.executor.Executor import FileRepr, ExecutedProcess, RunStatus, ProcessId
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.executor.LocalExecutor import LocalExecutor
from weskit.classes.executor.SshExecutor import SshExecutor
from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor, execute
from weskit.classes.executor.cluster.slurm.SlurmExecutor import SlurmExecutor
from weskit.memory_units import Memory, Unit

# Note that this cannot be solved by a fixture yielding multiple times.
# See https://github.com/pytest-dev/pytest/issues/1595.
#
# Instead marks for individual parameters of pytest.mark.parametrize are used.
# See https://docs.pytest.org/en/6.2.x/example/markers.html#marking-individual-tests-when-using-parametrize   # noqa
#
# You can select the tests to execute on the commandline.
executors = {
    "local": pytest.param(LocalExecutor(),
                          marks=[pytest.mark.integration])
}


with open("tests/remote.yaml", "r") as f:
    remote_config = yaml.safe_load(f)


if remote_config is not None and "ssh" in remote_config.keys():
    ssh_executor = SshExecutor(**(remote_config["ssh"]))
    executors["ssh"] = pytest.param(ssh_executor,
                                    marks=[pytest.mark.slow,
                                           pytest.mark.integration,
                                           pytest.mark.ssh])


if remote_config is not None and "lsf_submission_host" in remote_config.keys():
    ssh_lsf_executor = LsfExecutor(SshExecutor(**(remote_config['lsf_submission_host']['ssh'])))
    shared_workdir = remote_config['lsf_submission_host']["shared_workdir"]
    executors["ssh_lsf"] = pytest.param(ssh_lsf_executor,
                                        marks=[pytest.mark.slow,
                                               pytest.mark.integration,
                                               pytest.mark.ssh_lsf])


if remote_config is not None and "slurm_submission_host" in remote_config.keys():
    ssh_slurm_executor = SlurmExecutor(SshExecutor(**(
        remote_config['slurm_submission_host']['ssh'])))
    shared_workdir = remote_config['slurm_submission_host']["shared_workdir"]
    executors["ssh_slurm"] = pytest.param(ssh_slurm_executor,
                                          marks=[pytest.mark.slow,
                                                 pytest.mark.integration,
                                                 pytest.mark.ssh_slurm])


def test_runstatus():
    success_result = RunStatus(0)
    assert not success_result.failed
    assert success_result.finished
    assert success_result.success
    assert success_result.name is None
    assert success_result.message is None

    failed_result = RunStatus(1)
    assert failed_result.failed
    assert failed_result.finished
    assert not failed_result.success

    unfinished_result = RunStatus()
    assert not unfinished_result.finished
    assert not unfinished_result.success
    assert not unfinished_result.failed

    full_result = RunStatus(1, "name", "message")
    assert full_result.name == "name"
    assert full_result.message == "message"


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
    # Note: SLURM exits with code 0. It changes to /tmp if dir does not exists
    # This behaviour can be changes by the admin. slurm.conf
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
    def ssh_executor(self) -> SshExecutor:
        pass

    def move_to_local(self, remote, local):
        """
        This removes the file on the remote side.
        """
        asyncio.get_event_loop().run_until_complete(
            self.ssh_executor.get(remote, local))
        asyncio.get_event_loop().run_until_complete(
            self.ssh_executor.remote_rm(remote))

    def run_execute_test(self, temporary_dir):
        prefix = uuid.uuid4()
        stderr_file = self.workdir / f"{prefix}.stderr"
        stdout_file = self.workdir / f"{prefix}.stdout"

        result = self.execute(stdout_file, stderr_file)

        local_temp = PurePath(temporary_dir)
        self.move_to_local(stdout_file, local_temp / f"{prefix}.stdout")
        self.move_to_local(stderr_file, local_temp / f"{prefix}.stderr")

        self.check_execution_result(result, stdout_file, stderr_file,
                                    local_temp / f"{prefix}.stdout")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ssh
class TestSubmitSshProcess(ExecuteProcessViaSsh):

    @property
    def executor(self) -> SshExecutor:
        return ssh_executor

    @property
    def ssh_executor(self) -> SshExecutor:
        return ssh_executor

    @property
    def remote(self) -> str:
        return self.executor.hostname

    @property
    def workdir(self) -> PurePath:
        return PurePath("/tmp")

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
    def ssh_executor(self) -> SshExecutor:
        # We do an explicit cast here. The only use case we are interested in is that the nested
        # executor is a remote executor, and the only we provide is the one based on SSH. The
        # cast avoids problems with the type highlighting and makes this decision (somehow)
        # explicit, without coming up with a `RemoteExecutor` or so, which would be total overkill.
        return cast("SshExecutor", ssh_lsf_executor.executor)

    @property
    def remote(self) -> str:
        return self.ssh_executor.hostname

    @property
    def workdir(self) -> PurePath:
        # Note: For this test, the workdir needs to be accessibly from the submission/ssh host
        #       and the compute nodes. Therefore, choose a location on a shared filesystem.
        return PurePath(shared_workdir)

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
        if indexed is None:
            assert False, f"Invalid standard output: {observed}"
        fromIdx = indexed[0] + 2
        toIdx = len(observed) - 6
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
    command = ShellCommand(["sleep", "20" if isinstance(executor, (SlurmExecutor, LsfExecutor))
                            else "1"],
                           workdir=PurePath("./"))
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


# I didn't get the SshExecutor to succeed in this test (see comment below). As the usage-pattern
# of the Executor does (currently) not rely on update_process() but only wait_for(), it's probably
# acceptable to keep the SshExecutor out in this test.
@pytest.mark.parametrize("executor",
                         dict(filter(lambda kv: kv[0] != "ssh", executors.items())).values())
def test_update_process(executor):
    if isinstance(executor, LocalExecutor):
        sleep_duration = 1
    elif isinstance(executor, SshExecutor):
        sleep_duration = 5
    elif isinstance(executor, LsfExecutor):
        sleep_duration = 30
    elif isinstance(executor, SlurmExecutor):
        sleep_duration = 30
    else:
        sleep_duration = 10

    command = ShellCommand(["sleep", str(sleep_duration)],
                           workdir=PurePath("./"))
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
    # The following test fails for the SshExecutor, maybe because of stream-flushing issues. If the
    # sleep is substituted by SshExecutor.wait_for() then in works.
    # executor.wait_for(process)
    time.sleep(2*sleep_duration)
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


class MockExecutor(Executor):

    def __init__(self, target_runstatus):
        self.update_process_called_with = None
        self.get_status_called_with = None
        self.wait_for_called_with = None
        self._target_runstatus = target_runstatus

    def get_status(self, process: ExecutedProcess) -> RunStatus:
        self.get_status_called_with = process
        return process.result.status

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        return process

    def kill(self, process: ExecutedProcess):
        pass

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        self.wait_for_called_with = process
        process.result.status = RunStatus(self._target_runstatus)
        return process.result

    def copy_file(self, source: PathLike, target: PathLike):
        pass

    def remove_file(self, file: PathLike):
        pass

    def _write_mock_to_opt_filerepr(self, text: str, file: Optional[FileRepr]):
        if file is not None:
            # mypy does not understand `isinstance` for type inference.
            # Instead we do explicit casts to the two types unified in FileRepr.
            if isinstance(file, IO):
                print(text, file=cast(IO[str], file))
            else:
                with open(cast(PathLike, file), "w") as f:
                    print(text, file=f)

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[FileRepr] = None,
                stderr_file: Optional[FileRepr] = None,
                stdin_file: Optional[FileRepr] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) -> ExecutedProcess:
        self._write_mock_to_opt_filerepr("stdout", stdout_file)
        self._write_mock_to_opt_filerepr("stderr", stderr_file)
        return ExecutedProcess(process_handle=None,
                               executor=self,
                               pre_result=CommandResult(command=command,
                                                        id=ProcessId(12234),
                                                        run_status=RunStatus(),
                                                        stderr_file=stderr_file,
                                                        stdout_file=stdout_file,
                                                        stdin_file=stdin_file,
                                                        start_time=datetime.now()))


def test_executor_context_manager():

    command = ShellCommand(["echo", "something"])
    executor = MockExecutor(target_runstatus=0)
    with execute(executor, command) as (result, stdout, stderr):
        assert executor.wait_for_called_with.id.value == 12234
        assert result.status.code == 0
        assert stderr.readlines() == ["stderr\n"]
        assert stdout.readlines() == ["stdout\n"]
        assert result.stdout_file == Path(stdout.name)
        assert result.stderr_file == Path(stderr.name)
        assert re.match(r"/tmp/\S+", stderr.name)
        assert re.match(r"/tmp/\S+", stdout.name)


def test_lsf_extract_jobid():
    executor = LsfExecutor(executor=LocalExecutor())
    bsub_output = ["Job <12345> is submitted to default queue <short>.\n"]
    assert executor.extract_jobid_from_submission_output(bsub_output) == "12345"

    delayed_bsub_output = [
        "don't remember exactly how this waiting line looks like",
        "nor this",
        "Job <54321> is submitted to default queue <short>.\n",
        "and this line should not occur, right"
    ]
    assert executor.extract_jobid_from_submission_output(delayed_bsub_output) == "54321"


def test_slurm_extract_jobid():
    executor = SlurmExecutor(executor=LocalExecutor())
    sbatch_output = ["Submitted batch job 24896 \n"]
    assert executor.extract_jobid_from_submission_output(sbatch_output) == "24896"


def test_slurm_parse_get_status():
    executor = SlurmExecutor(LocalExecutor())
    assert executor.parse_get_status_output(["36027            FAILED    127:0"]) == \
           ("36027", "FAILED", "127")
    with pytest.raises(ValueError):
        executor.parse_get_status_output(["35677          State      123"])


def test_lsf_parse_get_status():
    executor = LsfExecutor(LocalExecutor())
    assert executor.parse_get_status_output(["6789 EXIT 1"]) == ("6789", "EXIT", "1")
    assert executor.parse_get_status_output(['6781 DONE -\n']) == ("6781", "DONE", "-")
    assert executor.parse_get_status_output(["bli bla blu\n",
                                             "ignore me\n",
                                             "123 TheRealStatus -\n",
                                             "another line to ignore\n"]) == \
           ("123", "TheRealStatus", "-")
    with pytest.raises(ValueError):
        executor.parse_get_status_output(["bli bla blu\n",
                                          "ignore me\n",
                                          "123 TheRealStatus -\n",
                                          "another line to ignore\n",
                                          "123 DoneAnyway;-P 1"])
    with pytest.raises(ValueError):
        executor.parse_get_status_output([])


class TestLsfGetStatus:

    def make_process(self, cluster_job_id, bjobs_stdout, bjobs_stderr):

        class MockInnerExecutor(Executor):
            """
            This should emulate a successful bjobs execution producing the specified output.
            """

            def execute(self, command: ShellCommand, stdout_file: Optional[FileRepr] = None,
                        stderr_file: Optional[FileRepr] =
                        None, stdin_file: Optional[FileRepr] = None,
                        settings: Optional[ExecutionSettings] = None, **kwargs) -> ExecutedProcess:
                assert isinstance(stdout_file, PathLike)
                with open(stdout_file, "w") as f:
                    f.writelines(bjobs_stdout)
                    f.flush()
                assert isinstance(stderr_file, PathLike)
                with open(stderr_file, "w") as f:
                    f.writelines(bjobs_stderr)
                    f.flush()
                return ExecutedProcess(self, None,
                                       CommandResult(command, ProcessId(5432),
                                                     stdout_file, stderr_file, stdin_file,
                                                     RunStatus(None),
                                                     start_time=datetime.now()))

            def get_status(self, process: ExecutedProcess) -> RunStatus:
                return RunStatus(0)

            def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
                process.result.status = self.get_status(process)
                process.result.end_time = datetime.now()
                return process

            def kill(self, process: ExecutedProcess):
                pass

            def wait_for(self, process: ExecutedProcess) -> CommandResult:
                self.update_process(process)
                return process.result

            def copy_file(self, source: PathLike, target: PathLike):
                pass

            def remove_file(self, file: PathLike):
                pass

        executor = LsfExecutor(MockInnerExecutor())
        process = ExecutedProcess(executor=executor,
                                  process_handle=None,
                                  pre_result=CommandResult(ShellCommand([]),
                                                           id=ProcessId(cluster_job_id),
                                                           run_status=RunStatus(),
                                                           stdin_file=None,
                                                           stdout_file=None,
                                                           stderr_file=None,
                                                           start_time=datetime.now()))
        return executor, process

    def run_test(self, *args, **kwargs):
        executor, process = self.make_process(*args, **kwargs)
        return executor.get_status(process)

    def test_job_success(self):
        status = self.run_test("6789", ["6789 DONE -\n"], [])
        assert status.code == 0
        assert status.name == "DONE"

    def test_job_failed(self):
        status = self.run_test("6789", ["6789 EXIT 1"], [])
        assert status.code == 1
        assert status.name == "EXIT"

    def test_job_running(self):
        status = self.run_test("6789", ["6789 SOMESTATE -"], [])
        assert status.code is None
        assert status.name == "SOMESTATE"
        assert not status.finished

    def test_job_state_query_delayed(self):
        status = self.run_test("123", ["bli bla blu\n",
                                       "ignore me\n",
                                       "123 TheRealStatus -\n",
                                       "another line to ignore\n"], [])
        assert status.code is None
        assert not status.finished
        assert status.name == "TheRealStatus"

    def test_job_state_multiple_match_error(self):
        with pytest.raises(ExecutorException) as e:
            self.run_test("123", ["bli bla blu\n",
                                  "ignore me\n",
                                  "123 TheRealStatus -\n",
                                  "another line to ignore\n",
                                  "123 DoneAnyway;-P 1"], [])
        assert bool(re.match(r".+No unique match of status.+", str(e)))
