# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
from unittest.mock import patch

from weskit import PathContext
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.tasks.SubmissionWorker import run_command


@pytest.fixture
def mock_executor():
    # Mocking the Executor class
    with patch('weskit.classes.executor2.Executor.Executor', autospec=True) as mock_executor:
        yield mock_executor.return_value


@pytest.fixture
def mock_database():
    # Mocking the Database class
    with patch('weskit.classes.Database.Database', autospec=True) as mock_database:
        yield mock_database.return_value


def test_submission_worker_run_command(mock_executor,
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
    run_command(command=command_obj,
                worker_context=context,
                executor_context=context,
                execution_settings=ExecutionSettings(),
                executor=mock_executor)

    # Assertions
    mock_executor.execute.assert_called_once()


def test_submission_worker_run_command_exception(mock_executor,
                                                 mock_database,
                                                 temporary_dir,
                                                 test_config):
    # Create a SubmissionWorker instance
    command = ShellCommand(command=["invalid_command"], workdir="/path/to/workdir")
    context = PathContext(data_dir=Path(temporary_dir).parent,
                          workflows_dir=Path(temporary_dir),
                          singularity_containers_dir=Path(temporary_dir))

    # Set up mock executor behavior to raise an exception
    mock_executor.execute.side_effect = Exception("Permission denied: '/path'")

    # Run the command
    with pytest.raises(Exception, match="Permission denied: '/path'"):
        run_command(command=command,
                    worker_context=context,
                    executor_context=context,
                    execution_settings=ExecutionSettings(),
                    executor=mock_executor)
