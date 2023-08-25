#  Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, TypeVar, Generic, Self

from weskit.utils import mop
from weskit.classes.executor.ProcessId import ProcessId, WESkitExecutionId

# Type alias.
Reason = str


# The type used to model the external states. Usually enum.
S = TypeVar("S")


class ExternalState(Generic[S], metaclass=ABCMeta):
    """
    Decorator for external states, i.e. states related to some non-WESkit internal execution system,
    like those modelled by the Executor subclasses. The external state `S` is usually modeled as a
    simple enumeration value. Python enumerations are singletons, and consequently, can only
    carry global state. This `ExternalState` class takes such an enum as a representation of the
    status name of the external system, and adds exit codes, timestamps, and reasons.

    The intended usage pattern is as follows

    ```python
    extern_state = as_external_state(YourHTCState.from_code(parsed_code),
                                     datetime.now(),
                                     parsed_message)
    ```

    The `ExternalState` should hold all information that are necessary to describe the known
    state of a job in the external executor in some detail. For WESkit not all these details are
    necessary, but they may be relevant for debugging.

    * is_known: Whether the state is currently known, i.e. currently not in Absent state.
    * terminal states are modelled as TerminalExternalState with an additional field exit_code.
    * reasons: A list of reasons (actually just strings) explaining the cause of the state.
    * observed at: A timestamp of the observation.
    """

    def __init__(self,
                 pid: ProcessId,
                 state: Optional[S],
                 reasons: Optional[List[Reason]] = None,
                 observed_at: Optional[datetime] = None):
        """
        Any state observed in the executor, is an ExecutionState. Usually, the `state` value is
        not `None` for known states and `None` for unknown states, but there may be exceptions.

        Each string should be one reason. Do not abuse the string-list to dump individual lines!
        The reason string could be a multiline string.

        We do not model state transition graphs for the `ExternalState`. Instead, each
        ExternalState will be mapped to some ExecutionState that models a simplified and
        generalized transition graph for WESkit.
        """
        self._pid = pid
        self._wrapped_state = state
        self._observed_at = observed_at if observed_at is not None else datetime.now()
        self._reasons = reasons if reasons is not None else []

    @property
    def pid(self) -> ProcessId:
        """
        The process or job ID assigned by the external system.
        """
        return self._pid

    @property
    def observed_at(self) -> datetime:
        return self._observed_at

    @property
    def reasons(self) -> List[Reason]:
        return self._reasons

    @property
    def wrapped_state(self) -> Optional[S]:
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

    @property
    def is_tombstone(self) -> bool:
        """
        A tombstone state is used by WESkit to mark the end of a sequence of external
        states and thus closes an `ExecutionState`.
        """
        return False

    def __str__(self) -> str:
        return f"{self.__class__}(" + ", ".join([
            f"pid={self.pid}",
            f"state={self.wrapped_state}",
            f"reasons={self.reasons}",
            f"observed_at={self.observed_at}"
        ]) + ")"


class UnknownExternalState(ExternalState[S]):
    """
    `UnknownExternalState` should be used to represent states that are not currently observable,
    e.g., due to network connectivity issues.
    """
    def __init__(self,
                 pid: ProcessId,
                 state: Optional[S] = None,
                 reasons: Optional[List[Reason]] = None,
                 observed_at: Optional[datetime] = None):
        """
        Note that `state` usually will be `None` but some executors may have a special state for
        unknown states.
        """
        super().__init__(pid, state, reasons, observed_at)

    @property
    def is_known(self) -> bool:
        return False


class TerminalExternalState(ExternalState[S]):
    """
    `TerminalExternalState` should be used to represent terminal external states, i.e. states
    that should never be left again.
    """

    def __init__(self,
                 pid: ProcessId,
                 state: Optional[S],
                 exit_code: Optional[int] = None,
                 reasons: Optional[List[Reason]] = None,
                 observed_at: Optional[datetime] = None):
        """
        `TerminalExecutionState`s may have an exit code associated.
        """
        super().__init__(pid, state, reasons, observed_at)
        self._exit_code = exit_code

    @property
    def exit_code(self) -> Optional[int]:
        return self._exit_code

    @property
    def is_terminal(self) -> bool:
        return True


class _TombstoneExternalState(ExternalState[S]):
    """
    `_TombstoneExternalState` is used to mark the end time of `ExecutionState`.
    """

    def __init__(self,
                 pid: ProcessId,
                 state: Optional[S],
                 observed_at: Optional[datetime] = None):
        """
        Use the state that is responsible for the tombstone as `state`, if one exists. If this
        tombstone is set, because the system gave up waiting for a state from the external
        job system, then you may also use `None` as `state`, or however an unknown state is
        represented by the external executor.
        """
        super().__init__(pid, state, observed_at=observed_at)

    def is_tombstone(self) -> bool:
        return True


class ExecutionState(Generic[S], metaclass=ABCMeta):
    """
    The `ExecutionState` classes model the state of execution of a process on an `Executor` in
    WESkit. `S` is the type of the external state class, e.g. enum.

    Specifically, `ExecutionStates` has multiple functions:

    1. It represents a generalized transition graph. In principle, only certain external state
       transitions should be allowed by the external system. In some cases, they may not be
       explicitly defined, or even discouraged (e.g. Kubernetes). We will anyway encode a mapping
       of external states to generalized `ExecutionState`s and let the `ExecutionState` follow a
       simplified state graph. The external job management decides, which state labels correspond
       to which `ExecutionState`.
    2. State tracking. A single `ExecutionState` may correspond to a sequence of observed external
       states. We allow ta add all observations that map to one `ExecutionState`. State transitions
       to a new `ExecutionState` are then explicitly modeled as new `ExecutionState` instance.

    Note: There is no unknown `ExecutionState`. If the `ExternalState` was unknown/unobserved for
          too long (e.g. due to network interruptions, downtimes, etc.), then some logic may
          choose to continue to wait for a recovery to the same state or to a state in the
          transitive closure of the `ExecutionState`, or it may use SystemError to indicate a
          final failure of the process.

    Note: The `ExecutionState` is not an "executor" state. In particular, errors of the executor,
          such as timeouts, etc., should not be modelled as individual `ExecutorState`s. However,
          if the executor fails terminally, it is necessary to put the execution of a process on that
          executor into a `SystemError`. The `ExternalState` that represents the execution states
          as represented by the executor, should then contain the failure reason in its `reasons`
          field.
    """

    def __init__(self,
                 execution_id: WESkitExecutionId,
                 external_state: Optional[ExternalState[S]],
                 previous_state: Optional[ExecutionState[S]]):
        """
        General purpose constructor that is only used by the `Start` state. In all other cases,
        use `from_previous(previous_state, external_state)`.
        """
        self._execution_id = execution_id
        self._previous_state = previous_state
        self._external_states = []
        if external_state is not None:
            self.add_observation(external_state)

    @classmethod
    def from_previous(cls,
                      previous_state: ExecutionState[S],
                      external_state: Optional[ExternalState[S]]) \
            -> Self:
        """
        To ensure continuity of the execution_id from state-to-state change you usually use this
        constructor function.

        :return An instance of cls, correctly typed. Compare https://peps.python.org/pep-0673/.
        """
        return cls(previous_state.execution_id, external_state, previous_state)

    @property
    def execution_id(self) -> WESkitExecutionId:
        return self._execution_id

    @property
    def ever_observed(self) -> bool:
        """
        The ExecutionState is not the initial state anymore, if at least one external state was
        observed. If the state was never queried or observed, this should return `False`.
        """
        return self.last_known_external_state is not None

    @property
    def external_pid(self) -> Optional[ProcessId]:
        """
        After successful submission there should be an external process ID.
        """
        if self.ever_observed:
            return self.last_external_state.pid
        else:
            return None

    @property
    def external_states(self) -> List[ExternalState[S]]:
        """
        Return the observed external states in order of observation (latest first).
        Multiple external states may map to the same `ExecutionState`. This is mostly meant
        for debugging and logging.

        Note that this list may be empty, if the process was not successfully submitted.
        """
        return self._external_states

    @property
    def created_at(self) -> Optional[datetime]:
        if self.ever_observed:
            return self.external_states[0].observed_at
        else:
            return None

    @property
    def last_external_state(self) -> Optional[ExternalState[S]]:
        """
        Return the last added external state.
        """
        if len(self.external_states) > 0:
            return self.external_states[-1]
        else:
            return None

    @property
    def previous_state(self) -> ExecutionState[S]:
        return self._previous_state

    @property
    def last_known_external_state(self) -> Optional[ExternalState[S]]:
        """
        Return the last known state. If the process was successfully submitted then there is also
        at a last known state (at least `Pending`).
        """
        if len(self.external_states) > 0:
            for state in reversed(self.external_states):
                if state.is_known:
                    return state
        else:
            return None

    @property
    def last_known_at(self) -> Optional[datetime]:
        """
        Get the timestamp of the last known state.
        """
        last_known_state = self.last_known_external_state
        if last_known_state is None:
            return None
        else:
            return last_known_state.observed_at

    @property
    def last_queried_at(self) -> Optional[datetime]:
        """
        Get the timestamp of the last query, the result of which may have been successful
        (a known state) or not (an unknown state).
        """
        if self.ever_observed:
            return self.last_external_state.observed_at
        else:
            return None

    def add_observation(self, new_state: ExternalState[S]) -> None:
        """
        Add new state. This may fail with a ValueError, if

            * the `ExecutionState` is closed
            * the new state has an earlier timestamp than the last added state

        Note that ExecutionState has no knowledge of the actual state transition graph for the
        external system.

        It is possible to add unknown external states
        """
        if self.ever_observed:
            if self.last_external_state.is_tombstone:
                raise ValueError(f"Cannot add new state to closed ExecutionState: {new_state} "
                                 f"added to {self}")
            elif new_state.observed_at < self.last_external_state.observed_at:
                raise ValueError("Tried to add state with earlier timestamp than last state: " +
                                 f"{self.last_external_state.wrapped_state} ({self.last_external_state.observed_at}) -/-> " +
                                 f"{new_state} ({new_state.observed_at})")
            else:
                self._external_states.append(new_state)
        else:
            self._external_states.append(new_state)

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        pass

    def close(self, tombstone: _TombstoneExternalState[S]) -> None:
        """
        Close this state. No further external states can be added after this method was called.
        """
        self.add_observation(tombstone)

    @property
    def is_closed(self) -> bool:
        return isinstance(self.last_external_state, _TombstoneExternalState)

    @property
    def lifetime(self) -> Optional[timedelta]:
        """
        The time between the creation of the state and the last added state, or its closing time.

        It is possible that the timespan includes unknown states after which the system went
        again into this state. For instance, an external state sequence

            Running -> Unknown -> Running

        will have a lifetime of the time between the first Running and the last Running state.

        For the sequence

            Running -> Unknown

        the lifetime will include the timestamp of the Unknown state.

        Usually, the lifetime will be requested for a closed state. E.g. for the sequence

            Running -> Unknown -> Tombstone

        the lifetime will be the time between the first Running and the Tombstone state.
        """
        if self.last_known_at is not None:
            return self.last_external_state.observed_at - self.created_at
        else:
            return None

    @property
    def name(self) -> str:
        """
        The state name is just the class name. This is used for comparisons, e.g. to detect
        state changes.
        """
        return str(self.__class__)

    def __str__(self) -> str:
        return f"{self.name}(" + ", ".join([
            f"execution_id={self.execution_id}"
            f"external_states={self.external_states}",
            f"is_closed={self.is_closed}"
        ]) + ")"


class NonTerminalExecutionState(Generic[S], ExecutionState[S], metaclass=ABCMeta):

    @property
    def is_terminal(self) -> bool:
        return True

    def add_observation(self, new_state: ExternalState[S]) -> None:
        if new_state.is_terminal:
            raise ValueError("NonTerminalExecutionState must not be fed with "
                             f"TerminalExternalStates: {new_state} added to {self}")
        super().add_observation(new_state)


class TerminalExecutionState(Generic[S], ExecutionState[S], metaclass=ABCMeta):

    def add_observation(self, new_state: ExternalState[S]) -> None:
        if not new_state.is_terminal:
            raise ValueError("NonTerminalExecutionState must not be fed with "
                             f"TerminalExternalStates: {new_state} added to {self}")
        super().add_observation(new_state)

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def exit_code(self) -> Optional[int]:
        """
        `TerminalExecutionState`s may have an `exit_code`, if it is Succeeded or Failed.

        But there are other terminal states which may not have an exit code. For e.g.
        Canceled it may even depend on the executor, whether a cancellation is associated with
        an exit code.
        """
        return mop(self.last_known_external_state,
                   lambda s: s.exit_code)


# The following subclasses model the simplified state graph for WESkit. The actual mapping of
# external states to these states is done in the external job management.

class Start(Generic[S], NonTerminalExecutionState[S]):
    """
    The initial Start state has just an execution ID. It represents the state of an even not yet
    submitted process, consequently there is no External state associated with the Start state.
    """

    def __init__(self,
                 execution_id: WESkitExecutionId):
        super().__init__(execution_id, None, None)


class Pending(Generic[S], NonTerminalExecutionState[S]):
    """
    The first state after submission. This could also be called "Submitted", but `Pending`
    should also be used for pending-like states in the external execution system.
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
ALLOWED_TRANSITIVE_TRANSITIONS = {
    str(k): [str(v) for v in vs]
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
            SystemError
        ],
        Pending: [
            Pending,
            Held,
            Running,
            Paused,
            Succeeded,
            Failed,
            Canceled,
            SystemError
        ],
        Held: [
            Held,
            Pending,
            Running,
            Succeeded,
            Failed,
            Paused,
            Canceled,
            SystemError
        ],
        Running: [
            Running,
            Paused,
            Succeeded,
            Failed,
            Canceled,
            SystemError
        ],
        Paused: [
            Paused,
            Running,
            Failed,
            Succeeded,
            Canceled,
            SystemError
        ],
        Failed: [
            Failed
            ],
        Succeeded: [
            Succeeded
        ],
        Canceled: [
            Canceled
        ],
        SystemError: [
            SystemError
        ]
    }.items()
}
