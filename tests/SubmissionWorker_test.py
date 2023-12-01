# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.classes.executor2.Executor import MockExecutor
from weskit.classes.Database import MockDatabase


@pytest.fixture
def mock_executor():
    return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')


@pytest.fixture
def mock_database():
    return MockDatabase()


@pytest.mark.asyncio
async def test_submission_worker_run_command(mock_executor,
                                             mock_database,
                                             temporary_dir,
                                             test_config):
    # Create a SubmissionWorker instance
    command = ["echo", "hello world", ss(">"), "x"]
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))
    workdir = Path(temporary_dir)
    command_obj = ShellCommand(command=command, workdir=workdir)

    # Run the command
    result = await run_command(command=command_obj,
                               worker_context=context,
                               executor_context=context,
                               execution_settings=ExecutionSettings(),
                               executor=mock_executor)
    assert result.execution_id is not None
    assert result.lifetime != 0
    assert result.is_terminal is False


def test_submission_worker_run_command_exception(mock_executor,
                                                 mock_database,
                                                 temporary_dir,
                                                 test_config):
    # Create a SubmissionWorker instance
    command = ShellCommand(command=["invalid_command"], workdir="/path/to/workdir")
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))

    # Run the command
    with pytest.raises(Exception, match="Permission denied: '/path'"):
        run_command(command=command,
                    worker_context=context,
                    executor_context=context,
                    execution_settings=ExecutionSettings(),
                    executor=mock_executor)
