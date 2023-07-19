#  Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Optional

from classes.executor.ProcessId import ProcessId
from weskit.classes.executor.ExecutionState import \
    Reason, ExternalState, UnknownExternalState, Pending, \
    Running, Succeeded, Failed
from weskit.classes.executor.StateMapper import SimpleStateMapper


class KubernetesPhase(Enum):
    Pending = auto()
    Running = auto()
    Succeeded = auto()
    Failed = auto()
    Unknown = auto()
    Terminating = auto()

    NOT_AVAILABLE = auto()

    @classmethod
    def from_state_name(cls, name: Optional[str]) -> KubernetesPhase:
        """
        Get Kubernetes phase from phase name.

        If phase name is not found, throw ValueError.
        """
        if name is None:
            return cls.NOT_AVAILABLE
        else:
            return cls[name]

    @classmethod
    def as_external_state(cls,
                          pid: ProcessId,
                          name: Optional[str],
                          observed_at: Optional[datetime] = None,
                          reason: Optional[Reason] = None) -> ExternalState[KubernetesPhase]:
        """
        Wrap the KubernetesPhase as `ExternalState` to provide the API necessary for the
        ExecutorState.

        Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
        """
        state = cls.from_state_name(name)
        if state == cls.Unknown:
            return UnknownExternalState(pid, cls.Unknown, [reason], observed_at)
        elif state == cls.NOT_AVAILABLE:
            return UnknownExternalState(pid, None, [reason], observed_at)
        else:
            return ExternalState(pid, state, [reason], observed_at)


state_mapper = SimpleStateMapper[KubernetesPhase]({
    KubernetesPhase.Pending: Pending,
    KubernetesPhase.Running: Running,
    KubernetesPhase.Terminating: Running,
    KubernetesPhase.Succeeded: Succeeded,
    KubernetesPhase.Failed: Failed
})
