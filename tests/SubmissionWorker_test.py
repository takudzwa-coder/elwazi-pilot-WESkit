# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
import os
import json

from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command
from weskit.classes.executor2.ProcessId import WESkitExecutionId
from weskit.classes.Run import Run
from Executor2_test import MockExecutor
from Database_test import MockDatabase
from Runs_test import mock_run_data


@pytest.fixture
def mock_executor():
    return MockExecutor(id=WESkitExecutionId(), log_dir_base='/path/to/log')


@pytest.fixture
def mock_database():
    return MockDatabase()


@pytest.mark.asyncio
def test_submission_worker_run_command(mock_executor,
                                       mock_database,
                                       temporary_dir,
                                       test_config):

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
    execution_log = run_command(command=command_obj,
                                worker_context=context,
                                executor_context=context,
                                execution_settings=ExecutionSettings(),
                                run_id=run.id,
                                executor=mock_executor,
                                database=mock_database
                                )

    print(execution_log)
    with open(os.path.join(temporary_dir, execution_log["log_file"]), "r") as f:
        command_result = json.load(f)
        assert command_result["workdir"] == str(workdir)
        assert command_result["cmd"] == [str(el) for el in command]
        assert command_result["exit_code"] is None
        assert command_result["start_time"]
        assert command_result["end_time"]
    assert execution_log["output_files"] is None


def test_submission_worker_run_command_exception(mock_executor,
                                                 mock_database,
                                                 temporary_dir,
                                                 test_config):

    run = Run(**mock_run_data)
    mock_database.insert_run(run)

    # Create a SubmissionWorker instance
    command = ShellCommand(command=["invalid_command"], workdir="/path/to/workdir")
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))

    # Run the command
    with pytest.raises(Exception, match="No such file or directory:"):
        run_command(command=command,
                    worker_context=context,
                    executor_context=context,
                    execution_settings=ExecutionSettings(),
                    run_id=run.id,
                    executor=mock_executor,
                    database=mock_database
                    )
