#  Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, Dict, Type, Callable, Optional

from weskit.classes.executor.ExecutionState \
    import ExecutionState, ExternalState, _TombstoneExternalState, ALLOWED_TRANSITIVE_TRANSITIONS

S = TypeVar("S")


class AbstractStateMapper(Generic[S],
                          # Callable[[ExecutionState[S], Optional[ExternalState[S]]], ExecutionState[S]],
                          metaclass=ABCMeta):
    """
    Abstract class for state mappers.

    Subclasses may use simple state-code to `ExecutorState` mappings, or may derive the
    `ExecutorState` also from `ExternalState.reasons` or `ExternalState.exit_code`.

    Subclasses may also handle unknown external states in different ways, e.g. by timing out
    after some time.

    This is a `Callable`. The usage pattern is

    ```python
    mapper = MyStateMapper()
    old_state, new_state = mapper(executor_state, external_state)
    ```
    """

    def _check_transition(self,
                          old_executor_state: ExecutionState[S],
                          suggested_executor_state: ExecutionState[S]):
        """
        Check whether a suggested transition is valid. Raise a RuntimeError, if that is not
        the case.
        """
        if suggested_executor_state.name not in\
                ALLOWED_TRANSITIVE_TRANSITIONS[old_executor_state.name]:
            raise RuntimeError(f"Forbidden state transition triggered by "
                               f"{suggested_executor_state.last_external_state}: "
                               f"{old_executor_state.name} -> {suggested_executor_state.name}")

    def _transition_to_next_state(self,
                                  old_executor_state: ExecutionState[S],
                                  suggested_executor_state: ExecutionState[S],
                                  **kwargs
                                  ) -> (ExecutionState[S], ExecutionState[S]):
        """
        Actually transition to the new state. This boils down to closing the current state,
        and returning the previously constructed suggested `new_executor_state` as
        new state.
        """
        self._check_transition(old_executor_state, suggested_executor_state)
        old_executor_state.close(_TombstoneExternalState[S].
                                 from_previous(suggested_executor_state.last_external_state))
        return suggested_executor_state

    def _accept_external_state(self,
                               executor_state: ExecutionState[S],
                               external_state: Optional[ExternalState[S]]
                               ) -> ExecutionState[S]:
        """
        Accept the observed `external_state` as member of the current `executor_state`.
        """
        executor_state.add_observation(external_state)
        return executor_state

    @abstractmethod
    def _suggest_next_state(self,
                            executor_state: ExecutionState[S],
                            external_state: Optional[ExternalState[S]],
                            *args,
                            **kwargs
                            ) -> ExecutionState[S]:
        """
        Suggest a next state. The possible next state is constructed, but nothing else. It may
        depend on the old `executor_state`, the observed `external_state`, and other contextual
        information (e.g. whether the process was sent a cancellation signal).
        """
        pass

    def _handle_unkown_external_state(self,
                                      executor_state: ExecutionState[S],
                                      external_state: Optional[ExternalState[S]],
                                      *args,
                                      **kwargs
                                      ) -> ExecutionState[S]:
        """
        By default, just accept unknown external states for as long as they persist. They are
        just added to the current state. This means, in principle wait forever for recovery
        and assume that all unknown states are actually the old state.
        """
        return self._accept_external_state(executor_state, external_state)

    # TODO Think! Return just new state? Keep ref to old state? Return also old state?
    def __call__(self,
                 executor_state: ExecutionState[S],
                 external_state: Optional[ExternalState[S]],
                 *args,
                 **kwargs
                 ) -> ExecutionState[S]:
        """
        Given an `ExecutorState` and an `ExternalState`, return the possibly
        modified `ExecutorState` (updated) the next `ExecutorState`. The `executor_state`
        may be modified in-place (by calling `add_observation` or `close`).

        :return: (updated_last_executor_state, new_executor_state)

        The new executor state may be the same as the old executor state, if no state transition
        is needed.

        This is a template method. Override the called methods to adapt the behaviour in the
        subclasses.
        """
        if not external_state.is_known:
            return self._handle_unkown_external_state(executor_state,
                                                      external_state,
                                                      *args,
                                                      **kwargs)
        else:
            suggested_next_state = self._suggest_next_state(executor_state,
                                                            external_state,
                                                            *args,
                                                            **kwargs)
            if executor_state.name == suggested_next_state.name:
                return self._accept_external_state(executor_state, external_state)
            else:
                return self._transition_to_next_state(executor_state, suggested_next_state)


class SimpleStateMapper(Generic[S], AbstractStateMapper[S]):
    """
    Takes a simple state-code-2-`ExecutorState` mapping at construction time. This is useful
    if the next state WESkit ExecutorState depends only on the `ExternalState`, but not, e.g.
    on an exit code, reason, or even more than the last `ExternalState`.
    """

    def __init__(self, state_map: Dict[S, Type[ExecutionState[S]]]):
        """
        The state_map should map `ExternalState` instances to `ExecutorState` classes. The
        classes are used to construct new `ExecutorState` instances.
        """
        self.state_map = state_map

    def _suggest_next_state(self,
                            executor_state: ExecutionState[S],
                            external_state: Optional[ExternalState[S]],
                            *args,
                            **kwargs
                            ) -> ExecutionState[S]:
        """
        This the simple strategy. Just consider the current state, and the external state to
        suggest a next state.
        """
        return self.state_map[external_state.state].from_previous(executor_state,
                                                                  external_state)
