# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
from abc import ABCMeta
import uuid
from werkzeug.utils import cached_property

from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command_impl, addID_to_run
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.classes.Run import Run
from weskit.tasks.SubmissionWorker import CommandTask
from weskit.classes.ProcessingStage import ProcessingStage

from MockExecutor_test import MockExecutor
from Database_test import MockDatabase


mock_run_data = {
    "id": uuid.uuid4(),
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


class CommandTaskMock(CommandTask, metaclass=ABCMeta):
    """
    Mock implementation of CommandTask.
    """

    @cached_property
    def executor(self):
        # Mocked executor for testing
        return MockExecutor(id=mock_run_data["id"])

    @cached_property
    def database(self):
        # Mocked database connection for testing
        return MockDatabase()


@pytest.mark.asyncio
async def test_submission_worker(temporary_dir,
                                 test_config):

    task = CommandTaskMock()

    run = Run(**mock_run_data)
    task.database.insert_run(run)

    # Add a WESkitExecutionId() to the run
    addID_to_run(task, run_id=run.id)

    # ID missing in current run dict
    assert run.execution_id is None

    run = task.database.get_run(run.id)
    # ID present run from DB
    assert isinstance(run.execution_id, WESkitExecutionId)

    command = ["echo", "hello world", ss(">"), "x"]
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))
    workdir = Path(temporary_dir)
    command_obj = ShellCommand(command=command, workdir=workdir)

    # Run the command
    await run_command_impl(
        task,
        command=command_obj,
        execution_settings=ExecutionSettings(),
        worker_context=context,
        executor_context=context,
        run_id=run.id
        )

    run = task.database.get_run(run.id)
    assert run.id == mock_run_data["id"]
    assert run.execution_log["cmd"] == ['echo', 'hello world', '>', 'x']
    assert isinstance(run.execution_id, WESkitExecutionId)
    assert run.processing_stage == "RUN_CREATED"
    assert run.state_log["executor_name"] == "MockExecutor"
    assert run.state_log["is_closed"] is False
