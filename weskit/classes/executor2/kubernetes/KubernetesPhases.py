# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from weskit.classes.executor2.ExecutionState import Failed, Pending, Running, Succeeded
from weskit.classes.executor2.ForeignState import (
    ForeignState,
    Reason,
    TerminalForeignState,
    UnidentifiedForeignState,
)
from weskit.classes.executor2.ProcessId import ProcessId
from weskit.classes.executor2.StateMapper import SimpleStateMapper


class KubernetesPhases(Enum):
    Pending = auto()
    Running = auto()
    Succeeded = auto()
    Failed = auto()
    Unknown = auto()
    Terminating = auto()

    UNDEFINED = auto()

    @classmethod
    def from_phase_name(cls, name: Optional[str]) -> KubernetesPhases:
        """
        Get Kubernetes phase from the pod phase name.
        """
        if name is None:
            return cls.UNDEFINED
        else:
            return cls[name]

    @classmethod
    def as_foreign_state(
        cls,
        pid: ProcessId,
        name: Optional[str],
        observed_at: Optional[datetime] = None,
        exit_code: Optional[int] = None,
        reason: Optional[Reason] = None,
    ) -> ForeignState[KubernetesPhases]:
        """
        Wrap the KubernetesPhase as `ForeignState` to provide the state necessary for the
        ExecutionState.

        For some reason if the state of the Pod could not be obtained then Unknown phase is
        automatically assigned by Kubernetes and we assume an Unidentified Foreign state in
        this case. This phase typically occurs due to an error in communicating with the node
        where the Pod should be running.

        In the case where the state(phase) of the Kubernetes system is not known, i.e., when name
        is None, we assign the state as UNDEFINED and assume an Unidentified Foreign State in
        this case.
        """
        try:
            state = cls.from_phase_name(name)
        except ValueError:
            return UnidentifiedForeignState(
                pid=pid,
                state=cls.Unknown,
                reason=f"Unknown state name: {name}",
                observed_at=observed_at,
            )
        if state == cls.UNDEFINED:
            return UnidentifiedForeignState(
                pid=pid,
                state=None,
                reason=cls.UNDEFINED.name,
                observed_at=observed_at,
            )
        elif state in [cls.Succeeded, cls.Failed]:
            return TerminalForeignState(
                pid=pid,
                state=state,
                exit_code=exit_code,
                reason=reason,
                observed_at=observed_at,
            )
        else:
            return ForeignState(
                pid=pid,
                state=state,
                reason=reason,
                observed_at=observed_at,
            )


class KubernetesStateMapper(SimpleStateMapper[KubernetesPhases]):
    """
    Mapping various Kubernetes Pod States to Execution states, to drive the executor API.

    Pod Phases and their lifecycle are modelled based on:
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
    """

    def __init__(self):
        super().__init__(
            {
                KubernetesPhases.Pending: Pending,
                KubernetesPhases.Running: Running,
                KubernetesPhases.Terminating: Running,
                KubernetesPhases.Succeeded: Succeeded,
                KubernetesPhases.Failed: Failed,
            }
        )
