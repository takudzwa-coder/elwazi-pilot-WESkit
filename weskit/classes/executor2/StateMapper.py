# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, Dict, Type

from weskit.classes.executor2.ExecutionState import (
    ExecutionState, ExternalState, ALLOWED_TRANSITIVE_TRANSITIONS, ObservedExecutionState, Start)

S = TypeVar("S")


class AbstractStateMapper(Generic[S],
                          metaclass=ABCMeta):
    """
    Abstract class for state mappers.

    Subclasses may use simple state-code to `ExecutionState` mappings, or may derive the
    `ExecutionState` also from `ExternalState.reasons` or `ExternalState.exit_code`.

    Subclasses may also handle unknown external states in different ways, e.g. by timing out
    after some time.

    This is a `Callable`. The usage pattern is

    ```python
    mapper = MyStateMapper()
    old_state, new_state = mapper(execution_state, external_state)
    ```
    """

    def _check_transition(self,
                          old_execution_state: ExecutionState[S],
                          suggested_execution_state: ObservedExecutionState[S]):
        """
        Check whether a suggested transition is valid. Raise a RuntimeError, if that is not
        the case.
        """
        if suggested_execution_state.name not in\
                ALLOWED_TRANSITIVE_TRANSITIONS[old_execution_state.name]:
            raise RuntimeError(f"Forbidden state transition triggered by "
                               f"{suggested_execution_state.last_external_state}: "
                               f"{old_execution_state.name} -> {suggested_execution_state.name}")

    def _transition_to_next_state(self,
                                  old_execution_state: ExecutionState[S],
                                  suggested_execution_state: ObservedExecutionState[S],
                                  **kwargs
                                  ) -> ObservedExecutionState[S]:
        """
        Actually transition to the new state. This boils down to closing the current state,
        and returning the previously constructed suggested `new_execution_state` as
        new state.
        """
        self._check_transition(old_execution_state, suggested_execution_state)
        old_execution_state.close(suggested_execution_state.last_external_state)
        return suggested_execution_state

    def _accept_external_state(self,
                               execution_state: ObservedExecutionState[S],
                               external_state: ExternalState[S]
                               ) -> ObservedExecutionState[S]:
        """
        Accept the observed `external_state` as member of the current `execution_state`.
        """
        execution_state.add_observation(external_state)
        return execution_state

    @abstractmethod
    def _suggest_next_state(self,
                            execution_state: ExecutionState[S],
                            external_state: ExternalState[S],
                            *args,
                            **kwargs
                            ) -> ObservedExecutionState[S]:
        """
        Suggest a next state. The possible next state is constructed, but nothing else. It may
        depend on the old `execution_state`, the observed `external_state`, and other contextual
        information (e.g. whether the process was sent a cancellation signal).
        """
        pass

    def _handle_unkown_external_state(self,
                                      execution_state: ObservedExecutionState[S],
                                      external_state: ExternalState[S],
                                      *args,
                                      **kwargs
                                      ) -> ObservedExecutionState[S]:
        """
        By default, just accept unknown external states for as long as they persist. They are
        just added to the current state. This means, in principle wait forever for recovery
        and assume that all unknown states are actually the old state.
        """
        return self._accept_external_state(execution_state, external_state)

    def __call__(self,
                 execution_state: ExecutionState[S],
                 external_state: ExternalState[S],
                 *args,
                 **kwargs
                 ) -> ObservedExecutionState[S]:
        """
        Given an `ExecutionState` and an `ExternalState`, return the possibly
        modified `ExecutionState` (updated), or the next `ExecutionState`. The `execution_state`
        will be modified in-place (by calling `add_observation` or `close`).

        :return: new_execution_state

        This is a template method. Override the called methods to adapt the behaviour in the
        subclasses.
        """
        if isinstance(execution_state, Start):
            # The Start state is special in that it is not observable and cannot keep track of
            # observations. This means, if we observe an external state we always want a new
            # state.
            return self._transition_to_next_state(
                execution_state,
                self._suggest_next_state(execution_state,
                                         external_state,
                                         *args, **kwargs))
        elif isinstance(execution_state, ObservedExecutionState):
            # This second isinstance() test really is only to satisfy the type inference.
            if not external_state.is_known:
                return self._handle_unkown_external_state(execution_state,
                                                          external_state,
                                                          *args,
                                                          **kwargs)
            else:
                suggested_next_state = self._suggest_next_state(execution_state,
                                                                external_state,
                                                                *args,
                                                                **kwargs)
                if execution_state.name == suggested_next_state.name:
                    return self._accept_external_state(execution_state, external_state)
                else:
                    return self._transition_to_next_state(execution_state, suggested_next_state)
        else:
            raise RuntimeError("Type error.")


class SimpleStateMapper(Generic[S], AbstractStateMapper[S]):
    """
    Takes a simple state-code-2-`ExecutionState` mapping at construction time. This is useful
    if the next state WESkit ExecutionState depends only on the `ExternalState`, but not, e.g.
    on an exit code, reason, or even more than the last `ExternalState`.
    """

    def __init__(self, state_map: Dict[S | None, Type[ObservedExecutionState[S]]]):
        """
        The state_map should map `ExternalState` instances to `ExecutionState` classes. The
        classes are used to construct new `ExecutionState` instances.
        """
        self.state_map = state_map

    def _suggest_next_state(self,
                            execution_state: ExecutionState[S],
                            external_state: ExternalState[S],
                            *args,
                            **kwargs
                            ) -> ObservedExecutionState[S]:
        """
        This the simple strategy. Just consider the current state, and the external state to
        suggest a next state.
        """
        return self.state_map[external_state.wrapped_state].from_previous(execution_state,
                                                                          external_state)
