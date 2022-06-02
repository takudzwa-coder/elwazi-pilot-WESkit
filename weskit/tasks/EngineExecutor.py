#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import logging
from enum import Enum

from weskit.classes.executor.Executor import Executor
from weskit.classes.executor.LocalExecutor import LocalExecutor
from weskit.classes.executor.SshExecutor import SshExecutor
from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor
from weskit.classes.executor.cluster.slurm.SlurmExecutor import SlurmExecutor

logger = logging.getLogger(__name__)


class EngineExecutorType(Enum):
    LOCAL = "local"
    LOCAL_LSF = "local_lsf"
    LOCAL_SLURM = "local_slurm"
    SSH = "ssh"
    SSH_LSF = "ssh_lsf"
    SSH_SLURM = "ssh_slurm"

    @property
    def executes_engine_locally(self) -> bool:
        return self == EngineExecutorType.LOCAL

    @property
    def executes_engine_remotely(self) -> bool:
        return not self.executes_engine_locally

    @property
    def needs_login_credentials(self) -> bool:
        return self.value.startswith("ssh")

    @staticmethod
    def from_string(name: str) -> EngineExecutorType:
        return EngineExecutorType[name.upper()]


def get_executor(executor_type: EngineExecutorType,
                 login_parameters: dict) -> Executor:
    executor: Executor
    executor_info = "".join(f"executor = {executor_type.name}")
    if executor_type.needs_login_credentials:
        if login_parameters is not None:
            if executor_type == EngineExecutorType.SSH:
                executor = SshExecutor(**login_parameters)
            elif executor_type == EngineExecutorType.SSH_LSF:
                executor = LsfExecutor(SshExecutor(**login_parameters))
            elif executor_type == EngineExecutorType.SSH_SLURM:
                executor = SlurmExecutor(SshExecutor(**login_parameters))
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
