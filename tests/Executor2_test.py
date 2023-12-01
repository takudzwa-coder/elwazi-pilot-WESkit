# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from signal import Signals
from typing import Optional, Dict, List
from time import sleep
from datetime import datetime, timedelta
import pytest

from urllib3.util.url import Url

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.ExecutionState import ExecutionState, ObservedExecutionState
from weskit.classes.executor2.ForeignState import ForeignState
from weskit.classes.executor2.ProcessId import WESkitExecutionId, ProcessId, Identifier
from weskit.classes.executor2.Executor import Executor
from weskit.classes.storage.StorageAccessor import StorageAccessor
from weskit.classes.executor2.Executor import ExecutionResult, ExecutionSettings


class MockExecutor(Executor[int]):
    def __init__(self, id: Identifier[str], log_dir_base: Optional[Path] = None):
        super().__init__(id, log_dir_base)
        self.execution_states: Dict[WESkitExecutionId, ExecutionState] = {}

    @property
    def hostname(self) -> str:
        return "localhost"

    async def execute(self,
                      execution_id: WESkitExecutionId,
                      command: ShellCommand,
                      stdout_file: Optional[Url] = None,
                      stderr_file: Optional[Url] = None,
                      stdin_file: Optional[Url] = None,
                      settings: Optional[ExecutionSettings] = None,
                      **kwargs) -> ExecutionState[int]:

        state: ExecutionState = MockExecutionState(execution_id,
                                                   created_at=datetime.now())
        self.execution_states[execution_id] = state
        return state

    async def get_status(self,
                         execution_id: WESkitExecutionId,
                         log_dir: Optional[Url] = None,
                         pid: Optional[int] = None) -> Optional[ExecutionState[int]]:
        return self.execution_states.get(execution_id)

    async def update_status(self,
                            current_state: ExecutionState[int],
                            log_dir: Optional[Url] = None,
                            pid: Optional[int] = None) -> Optional[ExecutionState[int]]:
        return self.execution_states.get(current_state.execution_id)

    async def get_result(self, state: ObservedExecutionState[int]) -> ExecutionResult[int]:
        return ExecutionResult(
            command=ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder")),
            stdout_url=None,
            stderr_url=None,
            stdin_url=None,
            state=state,
            start_time=state.created_at,
            end_time=state.created_at
        )

    async def kill(self,
                   state: ExecutionState[int],
                   signal: Signals) -> bool:
        # Send killing signal to process
        return True

    async def wait(self, state: ExecutionState[int]) -> None:
        # Waiting by sleeping for a short time
        sleep(2)

    @property
    def storage(self) -> StorageAccessor:
        mock_accessor = MockStorageAccessor()
        return mock_accessor


# The following line test the MockExecutor class
@pytest.fixture
def executor():
    return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')


@pytest.mark.asyncio
async def test_execute(executor):
    execution_id = WESkitExecutionId()
    command = ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder"))
    state = await executor.execute(execution_id, command)

    assert state  # Add more specific assertions based on your implementation
    assert isinstance(state, ExecutionState)
    assert state.execution_id == execution_id
    assert state.created_at is not None
    assert state.is_terminal is False
    assert state.lifetime != 0


@pytest.mark.asyncio
async def test_get_status(executor):
    execution_id = WESkitExecutionId()
    command = ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder"))
    await executor.execute(execution_id, command)

    current_state = await executor.get_status(execution_id)
    assert isinstance(current_state, ExecutionState)


@pytest.mark.asyncio
async def test_update_status(executor):
    execution_id = WESkitExecutionId()
    command = ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder"))
    state = await executor.execute(execution_id, command)

    updated_state = await executor.update_status(state)
    assert isinstance(updated_state, ExecutionState)


@pytest.mark.asyncio
async def test_get_result(executor):
    execution_id = WESkitExecutionId()
    command = ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder"))

    extern_state = ForeignState(ProcessId("12345", "localhost"),
                                state="Running",
                                observed_at=datetime.now())
    previous_state = MockExecutionState(execution_id, created_at=datetime.now())
    obs_state = MockObservedExecutionState(execution_id,
                                           external_state=extern_state,
                                           previous_state=previous_state)
    result = ExecutionResult(
            command=command,
            stdout_url=None,
            stderr_url=None,
            stdin_url=None,
            state=obs_state,
            start_time=previous_state.created_at,
            end_time=obs_state.created_at
        )

    res_command = result.command
    assert str(res_command) == str(command)
    res_process_id = result.process_id
    assert str(res_process_id) == str(ProcessId("12345", "localhost"))

    assert result.stdout_url is None
    assert result.stderr_url is None
    assert result.stdin_url is None
    assert result.state == obs_state
    assert result.start_time == previous_state.created_at
    assert result.end_time == obs_state.created_at


@pytest.mark.asyncio
async def test_wait(executor):

    execution_id = WESkitExecutionId()
    command = ShellCommand(["bash", "-c", "echo"], Path("/path/to/folder"))
    state = await executor.execute(execution_id, command)

    start = datetime.now()
    await executor.wait(state)
    end = datetime.now()
    time_diff = end.second - start.second
    assert time_diff == 2


# The MockStorageAccessor wont be tested now because it is not used in the Executor class
class MockStorageAccessor(StorageAccessor):

    async def put(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        print(f"Copying {source} to {target}")

    async def get(self, source: Path, target: Path,
                  recurse: bool = False,
                  dirs_exist_ok: bool = False) -> None:
        print(f"Copying {source} from {target}")

    async def remove_file(self, target: Path) -> None:
        print(f"Removing file at {target}")

    async def create_dir(self, target: Path, mode=0o077, exists_ok=False) -> None:
        print(f"Creating directory at {target}")

    async def remove_dir(self, target: Path, recurse: bool = False) -> None:
        print(f"Removing directory at {target}")

    async def find(self, target: Path) -> List[Path]:
        print(f"Finding files and subdirectories at {target}")
        return [Path("file1.txt"), Path("file2.txt"), Path("subdir")]


class MockExecutionState(ExecutionState[str]):

    def __init__(self, execution_id: WESkitExecutionId, created_at: Optional[datetime] = None):
        super().__init__(execution_id, created_at)

    @property
    def is_terminal(self) -> bool:
        return False

    def close(self, external_state: ForeignState[str]) -> None:
        super().close(external_state)

    @property
    def lifetime(self) -> Optional[timedelta]:
        return datetime.now() - self.created_at


# The following line test the MockExecutionState class
def test_mock_execution_state():
    execution_id = WESkitExecutionId()
    previous_state = MockExecutionState(execution_id, created_at=datetime.now())
    assert previous_state.is_terminal is False
    assert previous_state.lifetime != 0
    assert previous_state.execution_id == execution_id


class MockObservedExecutionState(ObservedExecutionState[str]):
    def __init__(self, execution_id: WESkitExecutionId,
                 external_state: ForeignState[str],
                 previous_state: ExecutionState[str]):
        super().__init__(execution_id, external_state, previous_state)

    def add_observation(self, new_state: ForeignState[str]) -> None:
        super().add_observation(new_state)

    def close(self, external_state: ForeignState[str]) -> None:
        super().close(external_state)

    @property
    def is_terminal(self) -> bool:
        return self.last_known_foreign_state.is_terminal


# The following line test the MockObservedExecutionState class
def test_mock_observed_execution_state():
    execution_id = WESkitExecutionId()
    process_id = ProcessId("12345", "localhost")
    previous_state = MockExecutionState(execution_id, created_at=datetime.now())
    external_state = ForeignState(process_id,
                                  state=None,
                                  observed_at=datetime.now())
    mock_observed_state = MockObservedExecutionState(execution_id,
                                                     external_state=external_state,
                                                     previous_state=previous_state)
    assert mock_observed_state.is_terminal is False
    assert mock_observed_state.execution_id == execution_id
    assert mock_observed_state.last_known_foreign_state == external_state
    assert mock_observed_state.lifetime != 0
    assert mock_observed_state.created_at is not None
