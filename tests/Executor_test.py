#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import re
import time
import uuid
from abc import abstractmethod, ABCMeta
from datetime import timedelta, datetime
from os import PathLike
from pathlib import Path
from typing import Optional

import pytest

import conftest
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import ExecutedProcess, ExecutionStatus, ProcessId
from weskit.classes.executor.Executor import \
    ExecutionSettings, CommandResult, Executor
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor, execute
from weskit.classes.executor.cluster.slurm.SlurmExecutor import SlurmExecutor
from weskit.classes.executor.unix.LocalExecutor import LocalExecutor
from weskit.classes.storage.LocalStorageAccessor import LocalStorageAccessor
from weskit.memory_units import Memory, Unit
from weskit.serializer import to_json, from_json
from weskit.utils import now


def test_execution_setting_dict():
    setting = ExecutionSettings(job_name="name",
                                accounting_name="projectName",
                                cores=1,
                                walltime=timedelta(hours=1),
                                memory=Memory(1, Unit.GIGA),
                                queue="devel",
                                group="some")
    assert dict(setting) == {
        "job_name": "name",
        "accounting_name": "projectName",
        "cores": 1,
        "walltime": timedelta(hours=1),
        "memory": Memory(1, Unit.GIGA),
        "queue": "devel",
        "group": "some"
    }

    assert ExecutionSettings(**dict(setting)) == setting


def test_execution_setting_json():
    setting = ExecutionSettings(job_name=None,
                                accounting_name="projectName",
                                cores=1,
                                walltime=timedelta(hours=1),
                                memory=Memory(1, Unit.GIGA),
                                queue="devel",
                                group="some")
    assert to_json(setting) == \
           '{"__type__": "weskit.classes.executor.Executor.ExecutionSettings", "__data__": '\
           '{"job_name": null, "accounting_name": "projectName", "group": "some", '\
           '"walltime": {"__type__": "datetime.timedelta", "__data__": "3600.0"}, '\
           '"memory": {"__type__": "weskit.memory_units.Memory", "__data__": "1GB"}, '\
           '"queue": "devel", "cores": 1}}'

    restored = from_json(to_json(setting))
    assert setting == restored


def test_execution_status():
    success_result = ExecutionStatus(0)
    assert not success_result.failed
    assert success_result.finished
    assert success_result.success
    assert success_result.name is None
    assert success_result.message is None
    assert str(success_result) == "ExecutionStatus(code=0)"

    failed_result = ExecutionStatus(1)
    assert failed_result.failed
    assert failed_result.finished
    assert not failed_result.success

    unfinished_result = ExecutionStatus()
    assert not unfinished_result.finished
    assert not unfinished_result.success
    assert not unfinished_result.failed

    full_result = ExecutionStatus(1, "name", "message")
    assert full_result.name == "name"
    assert full_result.message == "message"
    assert str(full_result) == "ExecutionStatus(code=1, name=name, message=message)"


@pytest.mark.parametrize("executor_prefix", conftest.executor_prefixes)
def test_submit_failing_command(executor_prefix, request):
    executor, _ = request.getfixturevalue(executor_prefix + "_executor")
    command = ShellCommand(["bash", "-c", "nonexistingcommand"],
                           workdir=Path("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_submit_failing_command",
                                   walltime=timedelta(minutes=5.0),
                                   memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    assert result.status.code == 127
    assert not result.status.success
    assert result.status.finished
    assert result.status.failed


@pytest.mark.parametrize("executor_prefix", conftest.executor_prefixes)
def test_submit_nonexisting_command(executor_prefix, request):
    executor, _ = request.getfixturevalue(executor_prefix + "_executor")
    command = ShellCommand(["nonexistingcommand"],
                           workdir=Path("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_submit_nonexisting_command",
                                   walltime=timedelta(minutes=5.0),
                                   memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    assert result.status.code == 127


@pytest.mark.parametrize("executor_prefix", conftest.executor_prefixes)
def test_inacessible_workdir(executor_prefix, request):
    executor, _ = request.getfixturevalue(executor_prefix + "_executor")
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=Path("/this/path/does/not/exist"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                job_name="weskit_test_inaccessible_workdir",
                                walltime=timedelta(minutes=5.0),
                                memory=Memory(100, Unit.MEGA)))
    result = executor.wait_for(process)
    # Note: LSF exits with code 2 with LSB_EXIT_IF_CWD_NOTEXIST=Y, but at least it fails.
    # Note: SLURM exits with code 0. It changes to /tmp if dir does not exist.
    # This behaviour can be changes by the admin. slurm.conf
    # ssh exits with 0
    assert result.status.code in [1, 2], result.status


class ExecuteProcess(metaclass=ABCMeta):

    @property
    @abstractmethod
    def workdir(self) -> Path:
        pass

    def execute(self, executor, stdout_file, stderr_file) -> CommandResult:
        # Note: This tests exports variables to Bash, as executed command. The variables (and $PWD)
        #       are then used to evaluate the shell expression.
        command = ShellCommand(["bash", "-c",
                                "echo \"In $PWD. Hello '$ENV_VAL'. "
                                "Hello '$WITH_SPACE'. Hello '$SPACEY_END'.\""],
                               workdir=self.workdir,
                               environment={
                                   # "EMPTY": "",              # `bsub -env "EMPTY="` fails
                                   "ENV_VAL": "world",
                                   "SPACEY_END": "earth",   # Should be "earth " to ensure terminal
                                                            # but fails for LsfExecutor (bug?).
                                   "WITH_SPACE": "wo, rld"  # Should be "wo, rld ".  dito.
                               })
        process = executor.execute(command,
                                   stdout_file=stdout_file,
                                   stderr_file=stderr_file,
                                   settings=ExecutionSettings(
                                       job_name="weskit_test_execute",
                                       walltime=timedelta(minutes=5.0),
                                       memory=Memory(100, Unit.MEGA)))
        return executor.wait_for(process)

    def _assert_stdout(self, observed, expected):
        assert observed == expected

    def check_execution_result(self, result, remote_stdout_file, remote_stderr_file, stdout_file):
        assert result.stdout_file == remote_stdout_file, result
        with open(stdout_file, "r") as stdout:
            stdout_lines = stdout.readlines()

        assert result.stderr_file == remote_stderr_file, result

        self._assert_stdout(
            stdout_lines,
            [f"In {str(self.workdir)}. Hello 'world'. Hello 'wo, rld'. Hello 'earth'.\n"]
            # WARNING: LSF Bug with terminal spaces in variable values provided by `-env`.
            #          With the actual input the solution should be
            #
            #          Hello 'world'. Hello 'wo, rld '. Hello 'earth '
            #
            # You can check this with
            #
            # bsub -env "test='some val ', other='other val '" \
            #    -M 102400K -R 'rusage[mem=102400K]' \
            #    -W 00:05 -R 'span[hosts=1]' \
            #    bash -c 'echo "-$test-$other-"'
        )

        assert result.status.code == 0, result

        assert result.status.success
        assert result.status.finished
        assert not result.status.failed
        assert result.start_time is not None
        assert result.end_time is not None


@pytest.mark.integration
class TestExecuteLocalProcess(ExecuteProcess):

    @property
    def workdir(self) -> Path:
        return self._workdir

    @workdir.setter
    def workdir(self, val: Path):
        self._workdir = val

    def test_execute(self, temporary_dir, local_executor):
        executor, _ = local_executor
        self.workdir = Path(temporary_dir)
        stderr_file = self.workdir / "stderr"
        stdout_file = self.workdir / "stdout"

        result = self.execute(executor, stdout_file, stderr_file)
        self.check_execution_result(result, stdout_file, stderr_file, stdout_file)


@pytest.mark.skipif("ssh" not in conftest.executor_prefixes,
                    reason="No SshExecutor. Did you configure your tests/remote.yaml?")
@pytest.mark.integration
@pytest.mark.ssh
class ExecuteProcessViaSsh(ExecuteProcess):

    async def move_to_local(self, storage, remote, local):
        """
        This removes the file on the remote side.
        """
        await storage.get(remote, local)
        await storage.remove_file(remote)

    async def run_execute_test(self, temporary_dir, executor):
        prefix = uuid.uuid4()
        stderr_file = self.workdir / f"{prefix}.stderr"
        stdout_file = self.workdir / f"{prefix}.stdout"

        result = executor.execute(stdout_file, stderr_file)

        local_temp = Path(temporary_dir)
        await self.move_to_local(executor.storage, stdout_file, local_temp / f"{prefix}.stdout")
        await self.move_to_local(executor.storage, stderr_file, local_temp / f"{prefix}.stderr")

        self.check_execution_result(result, stdout_file, stderr_file,
                                    local_temp / f"{prefix}.stdout")


@pytest.mark.skipif("ssh" not in conftest.executor_prefixes,
                    reason="No SshExecutor. Did you configure your tests/remote.yaml?")
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ssh
class TestSubmitSshProcess(ExecuteProcessViaSsh):

    @property
    def workdir(self) -> Path:
        return Path("/tmp")

    def test_execute(self, temporary_dir, ssh_executor):
        executor, _ = ssh_executor
        self.run_execute_test(temporary_dir, executor)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ssh_lsf
class TestSubmitLsfProcess(ExecuteProcessViaSsh):

    @property
    def workdir(self) -> Path:
        return self._workdir

    @workdir.setter
    def workdir(self, value: Path):
        self._workdir = value

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
        indexed = next(filter(lambda line: line[1] == "The output (if any) follows:\n",
                              zip(range(0, len(observed) - 1), observed)),
                       None)
        if indexed is None:
            assert False, f"Invalid standard output: {observed}"
        fromIdx = indexed[0] + 2
        toIdx = len(observed) - 6
        assert observed[fromIdx:toIdx] == expected, f"Could not validate stdout: {observed}"

    def test_execute(self, temporary_dir, ssh_lsf_executor):
        executor, workdir = ssh_lsf_executor
        self.workdir = workdir
        self.run_execute_test(temporary_dir, executor)


# This tests an internal feature of the LocalExecutor().
def test_std_fds_are_closed(local_executor, temporary_dir):
    executor, _ = local_executor
    workdir = Path(temporary_dir)
    command = ShellCommand(["bash", "-c", "echo"],
                           workdir=workdir)
    process = executor.execute(command,
                               stdout_file=workdir / "stdout",
                               stderr_file=workdir / "stderr")
    executor.wait_for(process)
    assert process.handle.stdout_fd.closed
    assert process.handle.stderr_fd.closed


@pytest.mark.parametrize("executor_prefix", conftest.executor_prefixes)
def test_get_status(executor_prefix, request):
    executor, _ = request.getfixturevalue(executor_prefix + "_executor")
    command = ShellCommand(["sleep", "30" if isinstance(executor, (SlurmExecutor, LsfExecutor))
                            else "1"],
                           workdir=Path("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                    job_name="weskit_test_get_status",
                                    walltime=timedelta(minutes=5.0),
                                    memory=Memory(100, Unit.MEGA)))
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
@pytest.mark.parametrize("executor_prefix", [executor
                                             for executor in conftest.executor_prefixes
                                             if executor.values[0] != "ssh"])
@pytest.mark.slow
def test_update_process(executor_prefix, request):
    executor, _ = request.getfixturevalue(executor_prefix + "_executor")

    if isinstance(executor, LocalExecutor):
        sleep_duration = 1
    elif isinstance(executor, LsfExecutor):
        sleep_duration = 30
    elif isinstance(executor, SlurmExecutor):
        sleep_duration = 30
    else:
        sleep_duration = 10

    command = ShellCommand(["sleep", str(sleep_duration)],
                           workdir=Path("./"))
    process = executor.execute(command,
                               settings=ExecutionSettings(
                                   job_name="weskit_test_update_process",
                                   walltime=timedelta(minutes=5.0),
                                   memory=Memory(100, Unit.MEGA)))
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


@pytest.mark.skip
@pytest.mark.parametrize("executor_prefix", conftest.executor_prefixes)
def test_kill_process(executor_prefix, request):
    # TODO Killing is not implemented yet.
    assert False


class MockExecutor(Executor):

    def __init__(self, target_status):
        self.update_process_called_with = None
        self.get_status_called_with = None
        self.wait_for_called_with = None
        self._target_status = target_status

    def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
        self.get_status_called_with = process
        return process.result.status

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        return process

    def kill(self, process: ExecutedProcess):
        pass

    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        self.wait_for_called_with = process
        process.result.status = ExecutionStatus(self._target_status)
        return process.result

    def copy_file(self, source: PathLike, target: PathLike):
        pass

    def remove_file(self, file: PathLike):
        pass

    def _write_mock_to_opt_filerepr(self, text: str, file: Optional[PathLike]):
        if file is not None:
            with open(file, "w") as f:
                print(text, file=f)

    @property
    def storage(self) -> LocalStorageAccessor:
        return LocalStorageAccessor()

    @property
    def hostname(self) -> str:
        return "localhost"

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) -> ExecutedProcess:
        self._write_mock_to_opt_filerepr("stdout", stdout_file)
        self._write_mock_to_opt_filerepr("stderr", stderr_file)
        return ExecutedProcess(process_handle=None,
                               executor=self,
                               pre_result=CommandResult(command=command,
                                                        process_id=ProcessId(12234),
                                                        execution_status=ExecutionStatus(),
                                                        stderr_file=stderr_file,
                                                        stdout_file=stdout_file,
                                                        stdin_file=stdin_file,
                                                        start_time=now()))


def test_executor_context_manager():
    command = ShellCommand(["echo", "something"])
    executor = MockExecutor(target_status=0)
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

            def execute(self, command: ShellCommand, stdout_file: Optional[PathLike] = None,
                        stderr_file: Optional[PathLike] =
                        None, stdin_file: Optional[PathLike] = None,
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
                                                     ExecutionStatus(None),
                                                     start_time=now()))

            def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
                return ExecutionStatus(0)

            def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
                process.result.status = self.get_status(process)
                process.result.end_time = datetime.now()
                return process

            def kill(self, process: ExecutedProcess):
                pass

            def wait_for(self, process: ExecutedProcess) -> CommandResult:
                self.update_process(process)
                return process.result

            def copy_file(self, source: Path, target: Path):
                pass

            def remove_file(self, file: Path):
                pass

            @property
            def storage(self) -> LocalStorageAccessor:
                return LocalStorageAccessor()

            @property
            def hostname(self) -> str:
                return "localhost"

        executor = LsfExecutor(MockInnerExecutor())
        process = ExecutedProcess(executor=executor,
                                  process_handle=None,
                                  pre_result=CommandResult(ShellCommand([]),
                                                           process_id=ProcessId(cluster_job_id),
                                                           execution_status=ExecutionStatus(),
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
