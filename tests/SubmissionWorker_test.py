# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
from abc import ABCMeta
from werkzeug.utils import cached_property

from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.classes.Run import Run
from Executor2_test import MockExecutor
from Database_test import MockDatabase
from weskit.tasks.SubmissionWorker import CommandTask
from weskit.classes.ProcessingStage import ProcessingStage


mock_run_data = {
    "id": WESkitExecutionId(),
    "processing_stage": ProcessingStage.RUN_CREATED,
    "request_time": None,
    "user_id": "test_id",
    "request": {
        "workflow_url": "",
        "workflow_params": '{"text":"hello_world"}'
    },
    "exit_code": None,
    "sub_dir": None
}

mock_run_data_2 = mock_run_data.copy()
mock_run_data_2["id"] = WESkitExecutionId()
mock_run_data_2["processing_stage"] = ProcessingStage.FINISHED_EXECUTION


class CommandTaskMock(CommandTask, metaclass=ABCMeta):
    """
    Mock implementation of CommandTask.
    """

    @cached_property
    def executor(self):
        # Mocked executor for testing
        return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')

    @cached_property
    def database(self):
        # Mocked database connection for testing
        return MockDatabase()


@pytest.mark.asyncio
async def test_submission_worker_run_command(temporary_dir,
                                             test_config):

    task = CommandTaskMock()

    run = Run(**mock_run_data)
    task.database.insert_run(run)

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
        event_loop=None
        )

    run = task.database.get_run(run.id)
    assert run.execution_log != {}
    assert run.processing_stage == 'RUN_CREATED'
