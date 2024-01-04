# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
from abc import ABCMeta
from werkzeug.utils import cached_property
from typing import Callable

from asyncio import AbstractEventLoop
from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.classes.Run import Run
from Executor2_test import MockExecutor
from Database_test import MockDatabase, mock_run_data
from weskit.utils import get_event_loop
from weskit.tasks.SubmissionWorker import CommandTask


@pytest.fixture
def mock_executor():
    return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')


@pytest.fixture
def mock_database():
    return MockDatabase()


class CommandTaskMock(CommandTask, metaclass=ABCMeta):
    """
    Mock implementation of CommandTask.
    """

    @cached_property
    def event_loop(self) -> AbstractEventLoop:
        return get_event_loop()

    @cached_property
    def executor(self):
        # Mocked executor for testing
        return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')

    @cached_property
    def database(self):
        # Mocked database connection for testing
        return MockDatabase()

    def run_sync(self, async_fun: Callable, *args, **kwargs):
        return self.event_loop.run_until_complete(async_fun(*args, **kwargs))


@pytest.mark.asyncio
async def test_submission_worker_run_command(mock_executor,
                                             mock_database,
                                             temporary_dir,
                                             test_config):

    task = CommandTaskMock()

    run = Run(**mock_run_data)
    mock_database.insert_run(run)

    # Create a SubmissionWorker instance
    command = ["echo", "hello world", ss(">"), "x"]
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))
    workdir = Path(temporary_dir)

    command_obj = ShellCommand(command=command, workdir=workdir)

    # Run the command
    await run_command(
        task,
        command=command_obj,
        worker_context=context,
        executor_context=context,
        execution_settings=ExecutionSettings(),
        run_id=run.id,
        executor=mock_executor,
        database=mock_database,
        event_loop=None
        )

    run = mock_database.get_run(run.id)
    assert run.execution_log != {}
    assert run.processing_stage == 'RUN_CREATED'
