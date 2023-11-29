# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import pytest
from weskit.classes.executor2.ProcessId import ProcessId, WESkitExecutionId
from weskit.classes.executor2.ExecutionState import (
    Failed,
    Pending,
    Running,
    Start,
    Succeeded,
)
from weskit.classes.executor2.kubernetes.KubernetesPhases import (
    KubernetesStateMapper,
    KubernetesPhases,
)


@pytest.mark.parametrize(
    "current_execution_state,"
    "previous_execution_state,"
    "previous_phase,"
    "current_phase,"
    "expected_execution_state",
    [
        (Pending, Start, "Pending", "Pending", Pending),
        (Pending, Start, "Pending", "Running", Running),
        (Pending, Start, "Running", "Terminating", Running),
        (Running, Pending, "Running", "Running", Running),
        (Running, Pending, "Terminating", "Terminating", Running),
        (Running, Pending, "Terminating", "Succeeded", Succeeded),
        (Running, Pending, "Terminating", "Failed", Failed),
        (Succeeded, Running, "Running", "Succeeded", Succeeded),
        (Failed, Running, "Terminating", "Failed", Failed),
    ],
)
def test_next_state_suggestion(
    current_execution_state,
    previous_execution_state,
    previous_phase,
    current_phase,
    expected_execution_state,
):
    processID = ProcessId(12234, "kubernetes")
    k8s_state_mapper = KubernetesStateMapper()
    previous_foreign_state = KubernetesPhases.as_foreign_state(
        pid=processID, name=previous_phase
    )
    current_execution_state = current_execution_state(
        execution_id=WESkitExecutionId(),
        foreign_state=previous_foreign_state,
        previous_state=previous_execution_state,
    )
    current_foreign_state = KubernetesPhases.as_foreign_state(
        pid=processID, name=current_phase
    )
    suggested_execution_state = k8s_state_mapper(
        execution_state=current_execution_state, foreign_state=current_foreign_state
    )
    assert suggested_execution_state.name() == expected_execution_state.name()


@pytest.mark.parametrize(
    "current_execution_state,"
    "previous_execution_state,"
    "previous_phase,"
    "current_phase,"
    "expected_execution_state",
    [
        (Failed, Failed, "Failed", "Running", Running),
    ],
)
def test_forbidden_next_state_transition(
    current_execution_state,
    previous_execution_state,
    previous_phase,
    current_phase,
    expected_execution_state,
):
    processID = ProcessId(12234, "kubernetes")
    k8s_state_mapper = KubernetesStateMapper()
    previous_foreign_state = KubernetesPhases.as_foreign_state(
        pid=processID, name=previous_phase
    )
    current_execution_state = current_execution_state(
        execution_id=WESkitExecutionId(),
        foreign_state=previous_foreign_state,
        previous_state=previous_execution_state,
    )
    current_foreign_state = KubernetesPhases.as_foreign_state(
        pid=processID, name=current_phase
    )
    with pytest.raises(RuntimeError) as error:
        k8s_state_mapper(
            execution_state=current_execution_state, foreign_state=current_foreign_state
        )
    assert (
        str(error.value)
        == f"Forbidden state transition triggered by {current_foreign_state.wrapped_state}:" +
        f" {current_execution_state.name()} -> {expected_execution_state.name()}"
    )
