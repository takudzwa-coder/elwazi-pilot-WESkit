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

from weskit.classes.executor.ProcessId import ProcessId
from weskit.classes.executor.StateMapper import SimpleStateMapper
from weskit.classes.executor.ExecutionState import ExternalState, Pending, Running, Succeeded, Failed, \
    UnknownExternalState, Reason, TerminalExternalState, Paused, Held


class LsfState(Enum):
    PEND = auto() 	    # Waiting in a queue for scheduling and dispatch.
    RUN = auto() 	    # Dispatched to a host and running
    DONE = auto() 	    # Finished normally with a zero exit value
    EXIT = auto() 	    # Finished with exit value != 0
    PSUSP = auto() 	    # Suspended by its owner or the LSF administrator while in PEND state
    USUSP = auto() 	    # Suspended by its owner or the LSF administrator after being dispatched
    SSUSP = auto() 	    # Suspended by the LSF system after being dispatched

    NOT_AVAILABLE = auto()  # Special state, if no values could be observed.

    @classmethod
    def from_state_name(cls,
                        code: Optional[str]) -> LsfState:
        """
        Get LsfState from state code.

        Throw ValueError, if state code is unknown.
        """
        if code is None:
            return cls.NOT_AVAILABLE
        else:
            return cls(code)

    @classmethod
    def as_external_state(cls,
                          job_id: ProcessId[str],
                          code: Optional[str],
                          exit_code: Optional[int] = None,
                          observed_at: Optional[datetime] = None,
                          reason: Optional[Reason] = None) -> ExternalState[LsfState]:
        """
        Wrap the LsfState as `ExternalState` to provide the API necessary for the ExecutorState.

        Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
        """
        lsf_state = cls.from_state_name(code)
        if lsf_state is cls.NOT_AVAILABLE:
            return UnknownExternalState(job_id, None, [reason], observed_at)
        if lsf_state in [cls.DONE, cls.EXIT]:
            return TerminalExternalState(job_id, lsf_state, exit_code, [reason], observed_at)
        else:
            return ExternalState(job_id, lsf_state, reason, observed_at)


# Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
get_next_state = SimpleStateMapper({
    LsfState.PEND: Pending,
    LsfState.RUN: Running,
    LsfState.DONE: Succeeded,
    LsfState.EXIT: Failed,
    LsfState.PSUSP: Held,
    LsfState.USUSP: Paused,
    LsfState.SSUSP: Paused,
})
