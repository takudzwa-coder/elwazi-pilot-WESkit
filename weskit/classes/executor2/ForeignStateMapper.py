# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import Generic, TypeVar, Dict

from weskit.classes.executor2.ForeignState import ForeignState, TerminalForeignState
from weskit.classes.executor2.ExecutionState import (Pending,
                                                     Running,
                                                     Succeeded,
                                                     Failed,
                                                     ExecutionState,
                                                     ObservedExecutionState)
from weskit.classes.executor2.StateMapper import SimpleStateMapper

S = TypeVar("S")


# The following foreign states are SLURM job states.
# The complete list can be found at:
# https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
# suffix fs stands for foreign state
class Pending_fs(Generic[S], ForeignState[S]):
    pass


class Running_fs(Generic[S], ForeignState[S]):
    pass


class Suspended_fs(Generic[S], ForeignState[S]):
    pass


class Canceled_fs(Generic[S], TerminalForeignState[S]):
    pass


class Failed_fs(Generic[S], TerminalForeignState[S]):
    pass


class Completing_fs(Generic[S], ForeignState[S]):
    pass


class Completed_fs(Generic[S], TerminalForeignState[S]):
    pass


class ForeignStates(Enum):
    Pending = Pending_fs
    Running = Running_fs
    Suspended = Suspended_fs
    Completing = Completing_fs


class TerminalState(Enum):
    Completed = Completed_fs
    Canceled = Canceled_fs
    Failed = Failed_fs


def map_foreign_state(foreign_state: ForeignState,
                      execution_state: ExecutionState) -> ExecutionState:

    foreign_state_map: Dict[Enum | None, type[ObservedExecutionState[Enum]]] = \
                        {
                            ForeignStates.Pending: Pending,
                            ForeignStates.Suspended: Pending,
                            ForeignStates.Running: Running,
                            ForeignStates.Completing: Running,
                            TerminalState.Completed: Succeeded,
                            TerminalState.Failed: Failed,
                            TerminalState.Canceled: Failed
                        }

    mapper = SimpleStateMapper(foreign_state_map)

    return mapper(execution_state, foreign_state)
