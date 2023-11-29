# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABCMeta
from datetime import datetime
from typing import Optional, TypeVar, Generic

from weskit.classes.executor2.ProcessId import ProcessId

# Type alias.
Reason = str


# The type used to model the foreign state set. The foreign state set are not explicitly modelled
# with all possible state transitions. Usually, they will just be modelled as enum.
S = TypeVar("S")


class ForeignState(Generic[S], metaclass=ABCMeta):
    """
    Decorator for foreign state set, i.e. states related to some non-WESkit internal execution
    system, like those modelled by the Executor subclasses. The foreign state set `S` is usually
    modeled as a simple enumeration value. Python enumerations are singletons, and consequently,
    can only carry global state. This `ForeignState` class takes such an enum as a representation
    of the status name of the foreign system, and adds exit codes, timestamps, and reasons.

    The intended usage pattern is as follows

    ```python
    foreign_state = as_foreign_state(YourHTCState.from_code(parsed_code),
                                     datetime.now(),
                                     parsed_message)
    ```

    The `ForeignState` should hold all information that are necessary to describe the known
    state of a job in the foreign executor in some detail. For WESkit not all these details are
    necessary, but they may be relevant for debugging.

    * is_known: Whether the state is currently known, i.e. currently not in Absent state.
    * terminal states are modelled as TerminalForeignState with an additional field exit_code.
    * reasons: A list of reasons (actually just strings) explaining the cause of the state.
    * observed at: A timestamp of the observation.
    """

    def __init__(
        self,
        pid: ProcessId,
        state: Optional[S],
        reason: Optional[Reason] = None,
        observed_at: Optional[datetime] = None,
    ):
        """
        Any state observed in the executor, is an ExecutionState. Usually, the `state` value is
        not `None` for known states and `None` for unknown states, but there may be exceptions.

        Each string should be one reason. Do not abuse the string-list to dump individual lines!
        The reason string could be a multiline string.

        We do not model state transition graphs for the `ForeignState`. Instead, each
        ForeignState will be mapped to some ExecutionState that models a simplified and
        generalized transition graph for WESkit.
        """
        self._pid = pid
        self._wrapped_state = state
        self._observed_at = observed_at if observed_at is not None else datetime.now()
        self._reason = reason

    @property
    def pid(self) -> ProcessId:
        """
        The process or job ID assigned by the foreign system.
        """
        return self._pid

    @property
    def observed_at(self) -> datetime:
        return self._observed_at

    @property
    def reason(self) -> Optional[Reason]:
        return self._reason

    @property
    def wrapped_state(self) -> Optional[S]:
        """
        If no state could be observed, then the wrapped_state may be None.
        """
        return self._wrapped_state

    @property
    def is_terminal(self) -> bool:
        """
        A terminal state is one that should not be left again, in particular not into a
        non-terminal state. We do not exclude the possibility that a job system reports a
        continuous sequence of different terminal states.
        """
        return False

    @property
    def is_known(self) -> bool:
        """
        A known state is one for which the job system successfully returned a state identifier.
        """
        return True

    def __str__(self) -> str:
        return (
            f"{self.__class__}("
            + ", ".join(
                [
                    f"pid={self.pid}",
                    f"state={self.wrapped_state}",
                    f"reason={self.reason}",
                    f"observed_at={self.observed_at}",
                ]
            )
            + ")"
        )


class UnidentifiedForeignState(ForeignState[S]):
    """
    `UnidentifiedForeignState` should be used to represent states that are not currently observable,
    e.g., due to network connectivity issues.
    """

    def __init__(
        self,
        pid: ProcessId,
        state: Optional[S] = None,
        reason: Optional[Reason] = None,
        observed_at: Optional[datetime] = None,
    ):
        """
        Note that `state` usually will be `None` but some executors may have a special state for
        unknown states.
        """
        super().__init__(pid, state, reason, observed_at)

    @property
    def is_known(self) -> bool:
        return False


class TerminalForeignState(ForeignState[S]):
    """
    `TerminalForeignState` should be used to represent terminal foreign states, i.e. states
    that should never be left again.
    """

    def __init__(
        self,
        pid: ProcessId,
        state: Optional[S],
        exit_code: Optional[int] = None,
        reason: Optional[Reason] = None,
        observed_at: Optional[datetime] = None,
    ):
        """
        `TerminalExecutionState`s may have an exit code associated.
        """
        super().__init__(pid, state, reason, observed_at)
        self._exit_code = exit_code

    @property
    def exit_code(self) -> Optional[int]:
        return self._exit_code

    @property
    def is_terminal(self) -> bool:
        return True
