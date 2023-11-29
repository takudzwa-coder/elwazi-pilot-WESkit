# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from signal import Signals
from typing import Optional, Dict, List
from time import sleep
from datetime import datetime, timedelta

from urllib3.util.url import Url

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.ExecutionState import ExecutionState, ObservedExecutionState
from weskit.classes.executor2.ExternalState import ExternalState
from weskit.classes.executor2.ProcessId import WESkitExecutionId, ProcessId, Identifier
from weskit.classes.executor2.Executor import Executor
from weskit.classes.storage.StorageAccessor import StorageAccessor
from weskit.classes.executor2.Executor import ExecutionResult, ExecutionSettings


class MockExecutor(Executor[int]):
    def __init__(self, id: Identifier[str], log_dir_base: Optional[Path] = None):
        super().__init__(id, log_dir_base)
        self.execution_states: Dict[WESkitExecutionId, ObservedExecutionState] = {}

    @property
    def hostname(self) -> str:
        return "mock_host"

    async def execute(self,
                      execution_id: WESkitExecutionId,
                      command: ShellCommand,
                      stdout_file: Optional[Url] = None,
                      stderr_file: Optional[Url] = None,
                      stdin_file: Optional[Url] = None,
                      settings: Optional[ExecutionSettings] = None,
                      **kwargs) -> ExecutionState[int]:
        state: ObservedExecutionState = mock_observed_state
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
            command=ShellCommand(["bash", "-c", "echo"], Path("/path/does/not/exist")),
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
        # Simulate killing
        return True

    async def wait(self, state: ExecutionState[int]) -> None:
        # Simulate waiting by sleeping for a short time
        sleep(0.1)

    @property
    def storage(self) -> StorageAccessor:
        # Return a dummy storage for testing ?
        # Not possible with abstract methods!
        mock_accessor = MockStorageAccessor()
        return mock_accessor


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


class MockObservedExecutionState(ObservedExecutionState[str]):
    def __init__(self, execution_id: WESkitExecutionId,
                 external_state: ExternalState[str],
                 previous_state: ExecutionState[str]):
        super().__init__(execution_id, external_state, previous_state)

    def add_observation(self, new_state: ExternalState[str]) -> None:
        super().add_observation(new_state)

    def close(self, external_state: ExternalState[str]) -> None:
        super().close(external_state)

    @property
    def is_terminal(self) -> bool:
        return self.last_known_external_state.is_terminal


class MockExecutionState(ExecutionState[str]):

    def __init__(self, execution_id: WESkitExecutionId, created_at: Optional[datetime] = None):
        super().__init__(execution_id, created_at)

    @property
    def is_terminal(self) -> bool:
        return False

    def close(self, external_state: ExternalState[str]) -> None:
        super().close(external_state)

    @property
    def lifetime(self) -> Optional[timedelta]:
        return datetime.now() - self.created_at


execution_id = WESkitExecutionId()
process_id = ProcessId("12345", "localhost")
previous_state: ExecutionState = MockExecutionState(execution_id, created_at=datetime.now())
external_state: ExternalState = ExternalState(process_id, state=None, observed_at=datetime.now())
mock_observed_state = MockObservedExecutionState(execution_id,
                                                 external_state=external_state,
                                                 previous_state=previous_state)
