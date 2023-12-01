# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, TypeVar, Generic, Self, cast, Dict

from weskit.classes.executor2.ForeignState import ForeignState, TerminalForeignState
from weskit.classes.executor2.ProcessId import ProcessId, WESkitExecutionId

# The type used to model the foreign states. Usually enum.
S = TypeVar("S")


class ExecutionState(Generic[S], metaclass=ABCMeta):
    """
    The `ExecutionState` classes model the state of execution of a process on an `Executor`.
    `S` is the type of the foreign state class, e.g. enum. It is considered in the `ExecutionState`
    only insofar as it is wrapped in an `ForeignState[S]`.

    Specifically, `ExecutionState[S]` has multiple functions:

    1. It represents a generalized transition graph. In principle, only certain foreign state
       transitions should be allowed by the foreign system. In some cases, they may not be
       explicitly defined, or even discouraged (e.g. Kubernetes). We will anyway encode a mapping
       of foreign states to generalized `ExecutionState`s and let the `ExecutionState` follow a
       simplified state graph. The external job management decides, which state labels correspond
       to which `ExecutionState`.
    2. State tracking. A single `ExecutionState` may correspond to a sequence of observed foreign
       states. We allow ta add all observations that map to one `ExecutionState`. State transitions
       to a new `ExecutionState` are then explicitly modeled as new `ExecutionState` instance.

    Note: There is no unknown `ExecutionState`. If the `ForeignState` was unknown/unobserved for
          too long (e.g. due to network interruptions, downtimes, etc.), then some logic may
          choose to continue to wait for a recovery to the same state or to a state in the
          transitive closure of the `ExecutionState`, or it may use SystemError to indicate a
          final failure of the process.

    Note: The `ExecutionState` is not an "executor" state. In particular, errors of the executor,
          such as timeouts, etc., should not be modelled as individual `ExecutionState`s. However,
          if the executor fails terminally, it may be appropriate to put the **execution** state of
          a process on that executor into a `SystemError`. The `ForeignState` that represents the
          execution states as represented by the executor, should then contain the failure reason
          in its `reasons` field.
    """

    def __init__(
        self, execution_id: WESkitExecutionId, created_at: Optional[datetime] = None
    ):
        self._execution_id = execution_id
        self._closed_by: Optional[ForeignState[S]] = None
        if created_at is None:
            created_at = datetime.now()
        self._created_at = created_at

    @property
    def execution_id(self) -> WESkitExecutionId:
        return self._execution_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        pass

    def close(self, foreign_state: ForeignState[S]) -> None:
        """
        Close this state. No further foreign states can be added after this method was called.

        If the ExecutionState is closed because of a transition to a new ExecutionState, use the
        ForeignState that triggered the transition as argument.

        If the ExecutionState is closed because of e.g. a timeout, use an `UnkownForeignState` as
        argument.
        """
        self._closed_by = foreign_state

    def closed_by(self) -> ForeignState[S]:
        if self._closed_by is not None:
            return self._closed_by
        else:
            raise ValueError(
                "Cannot retrieve closing ForeignState for a non-closed ExecutionState: "
                + str(self.execution_id)
            )

    @property
    def is_closed(self) -> bool:
        return self._closed_by is not None

    @property
    @abstractmethod
    def lifetime(self) -> Optional[timedelta]:
        pass

    @classmethod
    def name(cls) -> str:
        """
        The state name is just the class name. This is used for comparisons, e.g. to detect
        state changes.
        """
        return str(cls.__name__)


class MockExecutionState(ExecutionState[str]):

    def __init__(self, execution_id: WESkitExecutionId, created_at: Optional[datetime] = None):
        super().__init__(execution_id, created_at)

    @property
    def is_terminal(self) -> bool:
        return False

    def close(self, external_state: ForeignState[str]) -> None:
        super().close(external_state)

    @property
    def lifetime(self) -> Optional[timedelta]:
        return datetime.now() - self.created_at


class ObservedExecutionState(ExecutionState[S], metaclass=ABCMeta):
    """
    An `ObservedExecutionState` is modelled by a list of observations (`ForeignState`) and always
    references a previous `ExecutionState`, e.g. a `Start` state.
    """

    def __init__(
        self,
        execution_id: WESkitExecutionId,
        foreign_state: ForeignState[S],
        previous_state: ExecutionState[S],
    ):
        """
        The ObservedExecutionState has the creation time set to the observation time of the
        foreign state that triggered its creation.
        """
        super().__init__(execution_id, foreign_state.observed_at)
        self._previous_state = previous_state
        if not foreign_state.is_known:
            raise RuntimeError(
                "ObservedExecutionState can only be initialized with known foreign state"
            )
        self._foreign_states: List[ForeignState[S]] = [foreign_state]

    @classmethod
    def from_previous(
        cls, previous_state: ExecutionState[S], foreign_state: ForeignState[S]
    ) -> Self:
        """
        To ensure continuity of the execution_id from state-to-state change, you usually use this
        constructor function.

        :return An instance of cls, correctly typed. See `Self` type:
                https://peps.python.org/pep-0673/.
        """
        return cls(previous_state.execution_id, foreign_state, previous_state)

    @property
    def foreign_pid(self) -> ProcessId:
        return self.last_foreign_state.pid

    @property
    def foreign_states(self) -> List[ForeignState[S]]:
        """
        Return the observed foreign states in order of observation (latest first).
        """
        return self._foreign_states

    @property
    def last_foreign_state(self) -> ForeignState[S]:
        """
        Return the last added foreign state.
        """
        return self.foreign_states[-1]

    @property
    def previous_state(self) -> ExecutionState[S]:
        return self._previous_state

    @property
    def last_known_foreign_state(self) -> ForeignState[S]:
        """
        Return the last known state (i.e. not UnKnownForeignState). If the process was
        successfully submitted then there is also at a last known state (at least `Pending`).
        """
        for state in reversed(self.foreign_states):
            if state.is_known:
                return state
        raise RuntimeError(
            "Oops! Should not happen"
        )  # Condition ensured by constructor.

    def add_observation(self, new_state: ForeignState[S]) -> None:
        """
        Add new state. This may fail with a ValueError, if

            * the `ExecutionState` is closed
            * the new state has an earlier timestamp than the last added state

        Note that ExecutionState has no knowledge of the actual state transition graph for the
        foreign system.

        It is possible to add unknown foreign states
        """
        if self.is_closed:
            raise ValueError(
                f"Cannot add new state to closed ExecutionState: {new_state} "
                f"added to {self}"
            )
        elif new_state.observed_at < self.last_foreign_state.observed_at:
            raise ValueError(
                "Tried to add state with earlier timestamp than last state: "
                + f"{self.last_foreign_state.wrapped_state} "
                f"({self.last_foreign_state.observed_at}) -/-> "
                + f"{new_state} ({new_state.observed_at})"
            )
        else:
            self._foreign_states.append(new_state)

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        pass

    def close(self, foreign_state: ForeignState[S]) -> None:
        """
        Close this state. No further foreign states can be added after this method was called.

        If the ExecutionState is closed because of e.g. a timeout, use an `UnkownForeignState` as
        argument.
        """
        self.add_observation(foreign_state)
        super().close(foreign_state)

    @property
    def lifetime(self) -> Optional[timedelta]:
        """
        The time between the creation of the state and the last added state, or its closing time.

        It is possible that the timespan includes unknown states after which the system went
        again into this state. For instance, an foreign state sequence

            Running -> Unknown -> Running

        will have a lifetime of the time between the first Running and the last Running state.

        For the sequence

            Running -> Unknown

        the lifetime will include the timestamp of the Unknown state.

        Usually, the lifetime will be requested for a closed state. E.g. for the sequence

            Running -> Unknown -> Tombstone

        the lifetime will be the time between the first Running and the Tombstone state.
        """
        return self.last_foreign_state.observed_at - self.created_at

    def __str__(self) -> str:
        return (
            f"{self.name}("
            + ", ".join(
                [
                    f"execution_id={self.execution_id}"
                    f"foreign_states={self.foreign_states}",
                    f"is_closed={self.is_closed}",
                ]
            )
            + ")"
        )


class MockObservedExecutionState(ObservedExecutionState[str]):
    def __init__(self, execution_id: WESkitExecutionId,
                 external_state: ForeignState[str],
                 previous_state: ExecutionState[str]):
        super().__init__(execution_id, external_state, previous_state)

    def add_observation(self, new_state: ForeignState[str]) -> None:
        super().add_observation(new_state)

    def close(self, external_state: ForeignState[str]) -> None:
        super().close(external_state)

    @property
    def is_terminal(self) -> bool:
        return self.last_known_foreign_state.is_terminal


class NonTerminalExecutionState(
    Generic[S], ObservedExecutionState[S], metaclass=ABCMeta
):
    @property
    def is_terminal(self) -> bool:
        return False


class TerminalExecutionState(Generic[S], ObservedExecutionState[S], metaclass=ABCMeta):
    def add_observation(self, new_state: ForeignState[S]) -> None:
        if not new_state.is_terminal:
            raise ValueError(
                "TerminalExecutionState must not be fed with "
                f"NonTerminalForeignStates: {new_state} added to {self}"
            )
        super().add_observation(new_state)

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def exit_code(self) -> Optional[int]:
        """
        `TerminalExecutionState`s may have an `exit_code`, if it is `Succeeded` or `Failed`.

        But there are other terminal states that do not have an exit code. For e.g.
        `Canceled` it may even depend on the executor, whether a cancellation is associated with
        an exit code.
        """
        if isinstance(self.last_known_foreign_state, TerminalForeignState):
            return cast(TerminalForeignState, self.last_known_foreign_state).exit_code
        else:
            return None


# The following subclasses model the simplified state graph for WESkit. The actual mapping of
# foreign states to these states is done in the external job management.


class Start(ExecutionState[S]):
    """
    The Start state is not an ObservedExecutionState. It is used before any observations of state
    from the executor.
    """

    def __init__(self, execution_id: WESkitExecutionId):
        super().__init__(execution_id, datetime.now())
        self._closed_by: Optional[ForeignState[S]] = None

    @property
    def execution_id(self) -> WESkitExecutionId:
        return self._execution_id

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        return False

    def close(self, foreign_state: ForeignState[S]) -> None:
        """
        Close this state. No further foreign states can be added after this method was called.

        If the ExecutionState is closed because of a transition to a new ExecutionState, use the
        ForeignState that triggered the transition as argument.

        If the ExecutionState is closed because of e.g. a timeout, use an `UnkownForeignState` as
        argument.
        """
        self._closed_by = foreign_state

    def closed_by(self) -> ForeignState[S]:
        if self._closed_by is not None:
            return self._closed_by
        else:
            raise ValueError(
                "Cannot retrieve closing ForeignState for a non-closed ExecutionState: "
                + str(self.execution_id)
            )

    @property
    def is_closed(self) -> bool:
        return self._closed_by is not None

    @property
    def lifetime(self) -> Optional[timedelta]:
        """
        The Start state has no observations. Therefore, the lifetime of the start state is the
        time since the creation of the Start state.
        """
        return datetime.now() - self._created_at

    def __str__(self) -> str:
        return (
            f"{self.name}("
            + ", ".join(
                [f"execution_id={self.execution_id}" f"is_closed={self.is_closed}"]
            )
            + ")"
        )


class Pending(Generic[S], NonTerminalExecutionState[S]):
    """
    The first state after submission. This could also be called "Submitted", but `Pending`
    should also be used for pending-like states in the foreign execution system.
    """

    pass


class Running(Generic[S], NonTerminalExecutionState[S]):
    pass


class Held(Generic[S], NonTerminalExecutionState[S]):
    pass


class Paused(Generic[S], NonTerminalExecutionState[S]):
    pass


class Succeeded(Generic[S], TerminalExecutionState[S]):
    pass


class Failed(Generic[S], TerminalExecutionState[S]):
    pass


class Canceled(Generic[S], TerminalExecutionState[S]):
    pass


class SystemError(Generic[S], TerminalExecutionState[S]):
    pass


# The allowed state transitions accounting for multistep transitions. This is the precalculated
# transitive closure of the state transition graph.
# Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
ALLOWED_TRANSITIVE_TRANSITIONS: Dict[str, List[str]] = {
    k.__name__: [v.__name__ for v in vs]  # type: ignore
    # Change everything into strings. The classes below are used for programming convenience.
    for k, vs in {
        Start: [
            Start,
            Pending,
            Held,
            Running,
            Paused,
            Succeeded,
            Failed,
            Canceled,
            SystemError,
        ],
        Pending: [
            Pending,
            Held,
            Running,
            Paused,
            Succeeded,
            Failed,
            Canceled,
            SystemError,
        ],
        Held: [
            Held,
            Pending,
            Running,
            Succeeded,
            Failed,
            Paused,
            Canceled,
            SystemError,
        ],
        Running: [Running, Paused, Succeeded, Failed, Canceled, SystemError],
        Paused: [Paused, Running, Failed, Succeeded, Canceled, SystemError],
        Failed: [Failed],
        Succeeded: [Succeeded],
        Canceled: [Canceled],
        SystemError: [SystemError],
    }.items()
}
