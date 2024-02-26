# SPDX-FileCopyrightText: 2024 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
from typing import Optional

from asyncio import AbstractEventLoop

from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.executor2.EngineExecutorType import EngineExecutorType
from weskit.classes.executor2.Executor import Executor

logger = logging.getLogger(__name__)


def get_executor(executor_type: EngineExecutorType,
                 login_parameters: dict,
                 event_loop: Optional[AbstractEventLoop]) -> Executor:
    executor: Executor
    executor_info = f"executor = {executor_type.name}"
    if executor_type.needs_login_credentials:
        if login_parameters is not None:
            connection = RetryableSshConnection(**login_parameters)
            if event_loop is not None:
                event_loop.run_until_complete(connection.connect())
                # ssh_executor = SshExecutor(connection, event_loop)
                pass
            else:
                # ssh_executor = SshExecutor(connection)
                pass
            if executor_type == EngineExecutorType.SSH:
                # executor = ssh_executor
                pass
            elif executor_type == EngineExecutorType.SSH_LSF:
                # executor = LsfExecutor(ssh_executor)
                pass
            elif executor_type == EngineExecutorType.SSH_SLURM:
                # executor = SlurmExecutor(ssh_executor)
                pass
            else:
                raise RuntimeError("SSH executor not supported! " + executor_info)
        else:
            raise RuntimeError("Could not read executors login parameters! " + executor_info)
    else:
        if executor_type == EngineExecutorType.KUBERNETES:
            # executor = KubernetesExecutor()
            pass
            raise RuntimeError("Executor not supported! " + executor_info)
    return executor
