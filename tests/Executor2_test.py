# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from datetime import datetime
import pytest

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor2.ExecutionState import (ExecutionState,
                                                     MockExecutionState,
                                                     MockObservedExecutionState)
from weskit.classes.executor2.ForeignState import ForeignState
from weskit.classes.executor2.ProcessId import WESkitExecutionId, ProcessId
from weskit.classes.executor2.Executor import MockExecutor
from weskit.classes.executor2.Executor import ExecutionResult


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


# The following line test the MockExecutionState class
def test_mock_execution_state():
    execution_id = WESkitExecutionId()
    previous_state = MockExecutionState(execution_id, created_at=datetime.now())
    assert previous_state.is_terminal is False
    assert previous_state.lifetime != 0
    assert previous_state.execution_id == execution_id


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
