# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT


from weskit.classes.executor2.ExecutionState import Failed, Pending, Running, Succeeded
from weskit.classes.executor2.ForeignStateMapper import (ForeignStates,
                                                         TerminalState,
                                                         map_foreign_state)


def test_map_foreign_state():
    assert map_foreign_state(ForeignStates.Pending) == Pending
    assert map_foreign_state(ForeignStates.Running) == Running
    assert map_foreign_state(ForeignStates.Suspended) == Pending
    assert map_foreign_state(ForeignStates.Completing) == Running
    assert map_foreign_state(TerminalState.Completed) == Succeeded
    assert map_foreign_state(TerminalState.Failed) == Failed
    assert map_foreign_state(TerminalState.Canceled) == Failed

    # Test for invalid input
    invalid_state = object()
    try:
        map_foreign_state(invalid_state)
    except KeyError:
        assert True
    else:
        assert False, "Should raise KeyError for invalid state"
