# SPDX-FileCopyrightText: 2024 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from enum import Enum


class EngineExecutorType(Enum):
    KUBERNETES = "k8s"
    SSH = "ssh"
    SSH_LSF = "ssh_lsf"
    SSH_SLURM = "ssh_slurm"

    @property
    def executes_engine_k8s(self) -> bool:
        return self == EngineExecutorType.KUBERNETES

    @property
    def executes_engine_remotely(self) -> bool:
        return not self.executes_engine_k8s

    @property
    def needs_login_credentials(self) -> bool:
        return self.value.startswith("ssh")

    @staticmethod
    def from_string(name: str) -> EngineExecutorType:
        return EngineExecutorType[name.upper()]
