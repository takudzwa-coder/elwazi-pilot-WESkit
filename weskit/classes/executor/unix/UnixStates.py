#  Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Optional

from classes.executor.ProcessId import ProcessId
from weskit.classes.executor.ExecutionState \
    import ExecutionState, ExternalState, Succeeded, Failed, Running, SystemError, Paused, Reason, TerminalExternalState
from weskit.classes.executor.StateMapper import AbstractStateMapper


class UnixState(Enum):
    """
    The UNIX process states, as observed by e.g. `ps` or other sources.

    Here are the different values that the s, stat and state output specifiers of `ps` (header
    "STAT" or "S") will display to describe the state of a process:
    """
    InterruptibleSleep = auto()    # S interruptible sleep (waiting for an event to complete)
    Idle = auto()                  # I Idle kernel thread
    DiskSleep = auto()             # D uninterruptible sleep (usually IO)
    Running = auto()               # R running or runnable (on run queue)
    Stopped = auto()               # T stopped by job control signal
    TracingStopped = auto()        # t stopped by debugger during the tracing
    Zombie = auto()                # Z defunct ("zombie") process, terminated but not reaped by
                                   #   its parent
    Dead = auto()                  # X dead (should never be seen)

    Paging = auto()                # W paging (not valid since kernel version >= 2.6)
    Wakekill = auto()              # K (not valid since kernel version > 3.13)
    Parked = auto()                # P (not valid since kernel version > 3.13)

    NOT_AVAILABLE = auto()         # Special state, if no values could be observed.


    @classmethod
    def from_single_letter_code(cls,
                                code: Optional[str])\
            -> UnixState:
        if code is None:
            # If the state is not available, it just means the process is not in the process
            # table anymore.
            return cls.NOT_AVAILABLE
        else:
            return {
                "S": cls.InterruptibleSleep,
                "I": cls.Idle,
                "D": cls.DiskSleep,
                "R": cls.Running,
                "T": cls.Stopped,
                "t": cls.TracingStopped,
                "Z": cls.Zombie,
                "X": cls.Dead,
                "W": cls.Paging,
                "P": cls.Parked,
                "K": cls.Wakekill
            }[code]

    @classmethod
    def as_external_state(cls,
                          pid: Optional[ProcessId],
                          code: Optional[str],
                          exit_code: Optional[int] = None,
                          reason: Optional[Reason] = None,
                          observed_at: Optional[datetime] = None)\
            -> ExternalState[UnixState]:
        """
        Wrap the UnixState as `ExternalState` to provide the API necessary for the ExecutorState.

        Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806

        Note that the pid can be None. This is for the special case, where the submission to the
        external system failed so early that not even a process identifier was assigned by that
        system.
        """
        state = cls.from_single_letter_code(code)
        if state in [UnixState.Dead, UnixState.Zombie, UnixState.NOT_AVAILABLE]:
            # UNIX will not show any state, if the process has ended! Therefore, an unobservable
            # state could actually be a TerminalExternalState or a SystemError. Also, Dead and
            # Zombie states may be SystemError, Succeeded, or Failed, dependent on the exit code.
            # on whether the exit code is known!
            return TerminalExternalState(pid, state, exit_code, [reason], observed_at)
        else:
            return ExternalState(pid, state, [reason], observed_at)


class UnixStateMapper(AbstractStateMapper[UnixState]):

    def __init__(self):
        pass

    def _suggest_next_state(self,
                            executor_state: ExecutionState[UnixState],
                            external_state: ExternalState[UnixState],
                            **kwargs
                            ) -> ExecutionState[UnixState]:
        if external_state.state in [UnixState.Paging, UnixState.Parked, UnixState.Wakekill]:
            # States that should not occur for newer kernels.
            return SystemError.from_previous(executor_state, external_state)
        if isinstance(external_state, TerminalExternalState):
            if external_state.exit_code is None:
                return SystemError.from_previous(executor_state, external_state)
            elif external_state.exit_code == 0:
                return Succeeded.from_previous(executor_state, external_state)
            elif external_state.exit_code > 0:
                return Failed.from_previous(executor_state, external_state)
        elif external_state.state in [UnixState.Running,
                                      UnixState.InterruptibleSleep,
                                      UnixState.Idle,
                                      UnixState.DiskSleep,
                                      UnixState.TracingStopped]:
            return Running.from_previous(executor_state, external_state)
        elif external_state.state in [UnixState.Stopped]:
            return Paused.from_previous(executor_state, external_state)
        else:
            raise RuntimeError(f"Bug! Unhandled ExternalState '{external_state}'")
