# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from datetime import datetime, timedelta
from typing import TypeVar, Optional, List, Dict
from time import sleep
from signal import Signals

from urllib3.util.url import Url

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.ExecutionState import (ExecutionState,
                                                     ObservedExecutionState,
                                                     NonTerminalExecutionState)
from weskit.classes.executor2.ForeignState import ForeignState
from weskit.classes.executor2.ProcessId import WESkitExecutionId, ProcessId, Identifier
from weskit.classes.executor2.Executor import Executor, ExecutionSettings
from weskit.classes.storage.StorageAccessor import StorageAccessor

S = TypeVar("S")


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

    @property
    def lifetime(self) -> Optional[timedelta]:
        return datetime.now() - self.created_at


class MockExecutor(Executor[int]):
    def __init__(self, id: Identifier[str], log_dir_base: Optional[Path] = None):
        super().__init__(id, log_dir_base)
        self.execution_states: Dict[WESkitExecutionId, ExecutionState] = {}

    @property
    def hostname(self) -> str:
        return "MockExecutor"

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

    async def get_result(self, state: ObservedExecutionState[int]) \
            -> NonTerminalExecutionState[int]:
        return NonTerminalExecutionState(
            execution_id=state.execution_id,
            foreign_state=ForeignState(ProcessId("12345", "k8s"),
                                       state=None,
                                       observed_at=datetime.now()),
            previous_state=state
        )

    async def kill(self,
                   state: ExecutionState[int],
                   signal: Signals) -> bool:
        # Send killing signal to process
        return True

    async def wait(self, state: ExecutionState[int]) -> None:
        # Waiting by sleeping for a short time
        sleep(0.01)

    @property
    def storage(self) -> MockStorageAccessor:
        mock_accessor = MockStorageAccessor()
        return mock_accessor


class MockObservedExecutionState(ObservedExecutionState[str]):
    def __init__(self, execution_id: WESkitExecutionId,
                 external_state: ForeignState[str],
                 previous_state: ExecutionState[str]):
        super().__init__(execution_id, external_state, previous_state)

    @property
    def is_terminal(self) -> bool:
        return self.last_known_foreign_state.is_terminal
