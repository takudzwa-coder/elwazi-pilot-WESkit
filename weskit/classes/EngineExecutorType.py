#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations

from enum import Enum


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
