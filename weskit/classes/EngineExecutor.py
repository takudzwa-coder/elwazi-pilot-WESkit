#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import logging
from asyncio import AbstractEventLoop

from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.executor.Executor import Executor
from weskit.classes.executor.unix.LocalExecutor import LocalExecutor
from weskit.classes.executor.unix.SshExecutor import SshExecutor
from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor
from weskit.classes.executor.cluster.slurm.SlurmExecutor import SlurmExecutor

logger = logging.getLogger(__name__)


def get_executor(executor_type: EngineExecutorType,
                 login_parameters: dict,
                 event_loop: AbstractEventLoop) -> Executor:
    executor: Executor
    executor_info = "".join(f"executor = {executor_type.name}")
    if executor_type.needs_login_credentials:
        if login_parameters is not None:
            connection = RetryableSshConnection(**login_parameters)
            event_loop.run_until_complete(connection.connect())
            ssh_executor = SshExecutor(connection, event_loop)
            if executor_type == EngineExecutorType.SSH:
                executor = ssh_executor
            elif executor_type == EngineExecutorType.SSH_LSF:
                executor = LsfExecutor(ssh_executor)
            elif executor_type == EngineExecutorType.SSH_SLURM:
                executor = SlurmExecutor(ssh_executor)
            else:
                raise RuntimeError("SSH executor not supported! " + executor_info)
        else:
            raise RuntimeError("Could not read executors login parameters! " + executor_info)
    else:
        if executor_type == EngineExecutorType.LOCAL:
            executor = LocalExecutor()
        elif executor_type == EngineExecutorType.LOCAL_LSF:
            executor = LsfExecutor(LocalExecutor())
        elif executor_type == EngineExecutorType.LOCAL_SLURM:
            executor = SlurmExecutor(LocalExecutor())
        else:
            raise RuntimeError("Local executor not supported! " + executor_info)
    return executor
