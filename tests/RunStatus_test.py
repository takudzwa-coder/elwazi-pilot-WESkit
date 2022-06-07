#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import pytest

from weskit.classes.RunStatus import RunStatus


def test_runstatus_is_pausible():
    assert not RunStatus.INITIALIZING.is_pausible
    assert RunStatus.RUNNING.is_pausible
    assert RunStatus.QUEUED.is_pausible


def test_runstatus_precedence():
    assert RunStatus.INITIALIZING.precedence < RunStatus.QUEUED.precedence
    for running_state in RunStatus.RUNNING_STATES():
        for terminal_state in RunStatus.TERMINAL_STATES():
            assert running_state.precedence < terminal_state.precedence


def test_runstatus_allowed_to_progress_to():  # noqa C901
    for a_state in RunStatus:
        for b_state in RunStatus:

            if a_state == b_state:
                assert a_state.progress_to(b_state)

            elif a_state == RunStatus.SYSTEM_ERROR and b_state != RunStatus.SYSTEM_ERROR:
                assert b_state.allowed_to_progress_to(a_state), [a_state, b_state]
                assert not a_state.allowed_to_progress_to(b_state), [a_state, b_state]
            elif b_state == RunStatus.SYSTEM_ERROR and a_state != RunStatus.SYSTEM_ERROR:
                assert not b_state.allowed_to_progress_to(a_state), [a_state, b_state]
                assert a_state.allowed_to_progress_to(b_state), [a_state, b_state]

            elif a_state.is_terminal and b_state.is_terminal:
                assert not a_state.allowed_to_progress_to(b_state), [a_state, b_state]
            elif a_state.is_terminal:
                assert b_state.allowed_to_progress_to(a_state), [a_state, b_state]
                assert not a_state.allowed_to_progress_to(b_state), [a_state, b_state]
            elif b_state.is_terminal:
                assert not b_state.allowed_to_progress_to(a_state), [a_state, b_state]
                assert a_state.allowed_to_progress_to(b_state), [a_state, b_state]

            elif (a_state == RunStatus.PAUSED and b_state.is_pausible) \
                    or (a_state.is_pausible and b_state == RunStatus.PAUSED):
                assert a_state.allowed_to_progress_to(b_state), [a_state, b_state]
                assert b_state.allowed_to_progress_to(a_state), [a_state, b_state]

            elif a_state == RunStatus.RUNNING and b_state == RunStatus.QUEUED:
                assert a_state.allowed_to_progress_to(b_state)

            elif b_state == RunStatus.INITIALIZING and a_state != RunStatus.INITIALIZING:
                assert not a_state.allowed_to_progress_to(b_state)

            elif a_state.precedence < b_state.precedence:
                assert a_state.allowed_to_progress_to(b_state), [a_state, b_state]

            else:
                assert not a_state.allowed_to_progress_to(b_state), [a_state, b_state]


def test_runstatus_progress_state():
    for a_state in RunStatus:
        for b_state in RunStatus:
            if a_state.allowed_to_progress_to(b_state):
                assert a_state.progress_to(b_state)
            else:
                with pytest.raises(RuntimeError):
                    a_state.progress_to(b_state)
