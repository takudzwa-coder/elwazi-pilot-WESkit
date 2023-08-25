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
from weskit.classes.executor.ExecutionState import Reason, ExternalState, UnknownExternalState, TerminalExternalState, \
    Failed, Succeeded, Pending, Running, Paused, Canceled, SystemError, Held
from weskit.classes.executor.StateMapper import SimpleStateMapper


# flake8: noqa: E116


class SlurmState(Enum):
    COMPLETED = auto()      # CD  has completed successfully.
    FAILED = auto()       	# F   terminated with a non-zero exit code and failed to execute.
    PENDING = auto()       	# PD  is waiting for resource allocation. It will eventually run.
    PREEMPTED = auto()      # PR  was terminated because of preemption by another job.
    RUNNING = auto()       	# R   currently is allocated to a node and is running.
    STOPPED = auto()       	# ST  has an allocation, but execution has been stopped with SIGSTOP
                            # signal. CPUs have been retained by this job.
    BOOT_FAIL = auto()      # BF  terminated due to launch failure, typically due to a hardware
                            # failure (e.g. unable to boot the node or block and the job can not
                            # be re-queued).
    CANCELLED = auto()      # CA  explicitly cancelled by the user or system administrator. The
                            # job may or may not have been initiated.
    CONFIGURING = auto()    # CF  has been allocated resources, but are waiting for them to become
                            # ready for use (e.g. booting).
    COMPLETING = auto()   	# CG  in the process of completing. Some processes on some nodes may
                            # still be active.
    STAGE_OUT = auto()      # SO  staging out files.
    SIGNALING = auto()      # SI  being signaled.
    DEADLINE = auto()       # DL  terminated on deadline.
    TIMEOUT = auto()       	# TO  terminated upon reaching its time limit.
    NODE_FAIL = auto()      # NF  terminated due to failure of one or more allocated nodes.
    OUT_OF_MEMORY = auto()  # OOM experienced out of memory error.

    REQUEUE_FED = auto()    # RF  being requeued by a federation.
    REQUEUE_HOLD = auto()   # RH  Held job is being requeued.
    RESV_DEL_HOLD = auto()  # RD  being held after requested reservation was deleted.
    REQUEUED = auto()       # RQ  Completing job is being requeued. The job will be requeued back
                            # in the PENDING state and scheduled again.
    SUSPENDED = auto()      # S   A running job has been stopped with its cores released to
                            # other jobs.
    RESIZING = auto()       # RS  about to change size.
    REVOKED = auto()       	# RV  Sibling was removed from cluster due to other cluster starting
                            # the job. federated clusters.
    SPECIAL_EXIT = auto()   # SE  The job was requeued in a special state. This state can be set
                            # by users, typically in EpilogSlurmctld, if the job has terminated
                            # with a particular exit value.

    NOT_AVAILABLE = auto()  # Special state, if no values could be observed.

    @classmethod
    def from_state_name(cls,
                        name: Optional[str])\
            -> SlurmState:
        """
        Get the SlurmState from a name string.

        Throws a ValueError, if state cannot be mapped.
        """
        if name is None:
            return cls.NOT_AVAILABLE
        else:
            return cls[name]

    @classmethod
    def from_state_code(cls,
                        code: Optional[str])\
            -> SlurmState:
        """
        Get the SlurmState form the name code (1-2 letters).

        Throws a ValueError, if state cannot be mapped.
        """
        if code is None:
            return cls.NOT_AVAILABLE
        else:
            return {
                "CD": cls.COMPLETED,
                "F": cls.FAILED,
                "PD": cls.PENDING,
                "PR": cls.PREEMPTED,
                "R": cls.RUNNING,
                "ST": cls.STOPPED,
                "BF": cls.BOOT_FAIL,
                "CA": cls.CANCELLED,
                "CF": cls.CONFIGURING,
                "CG": cls.COMPLETING,
                "SO": cls.STAGE_OUT,
                "SI": cls.SIGNALING,
                "DL": cls.DEADLINE,
                "TO": cls.TIMEOUT,
                "NF": cls.NODE_FAIL,
                "OOM": cls.OUT_OF_MEMORY,
                "RF": cls.REQUEUE_FED,
                "RH": cls.REQUEUE_HOLD,
                "RD": cls.RESV_DEL_HOLD,
                "RQ": cls.REQUEUED,
                "S": cls.SUSPENDED,
                "RS": cls.RESIZING,
                "RV": cls.REVOKED,
                "SE": cls.SPECIAL_EXIT
            }[code]

    @classmethod
    def as_external_state(cls,
                          job_id: Optional[ProcessId],
                          code: Optional[str],
                          exit_code: Optional[int] = None,
                          observed_at: Optional[datetime] = None,
                          reason: Optional[Reason] = None) -> ExternalState[SlurmState]:
        """
        Wrap the LsfState as `ExternalState` to provide the API necessary for the ExecutorState.

        Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
        """
        state = cls.from_state_name(code)
        if state is None:
            return UnknownExternalState(job_id, None, [reason], observed_at)
        elif state in [
            cls.COMPLETED,
            cls.FAILED,
            cls.CANCELLED,
            cls.BOOT_FAIL,
            cls.PREEMPTED,
            cls.DEADLINE,
            cls.NODE_FAIL,
            cls.OUT_OF_MEMORY,
            cls.TIMEOUT,
            # These map to system error. For now, we assume all these are also terminal states.
            cls.REQUEUE_FED,
            cls.REQUEUED,
            cls.REQUEUE_HOLD,
            cls.RESV_DEL_HOLD,
            cls.RESIZING,
            cls.REVOKED,
            cls.SPECIAL_EXIT
        ]:
            return TerminalExternalState(job_id, state, exit_code, [reason], observed_at)
        else:
            return ExternalState(job_id, state, [reason], observed_at)


# Compare Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/157#note_1190792806
state_mapper = SimpleStateMapper[SlurmState]({
    SlurmState.COMPLETED: Succeeded,
    SlurmState.FAILED: Failed,
    SlurmState.PENDING: Pending,
    SlurmState.PREEMPTED: Failed,
    SlurmState.RUNNING: Running,
    SlurmState.STOPPED: Paused,
    SlurmState.BOOT_FAIL: Failed,
    SlurmState.CANCELLED: Canceled,
    SlurmState.CONFIGURING: Running,
    SlurmState.COMPLETING: Running,
    SlurmState.STAGE_OUT: Running,
    SlurmState.SIGNALING: Running,
    SlurmState.DEADLINE: Failed,
    SlurmState.TIMEOUT: Failed,
    SlurmState.NODE_FAIL: Failed,
    SlurmState.OUT_OF_MEMORY: Failed,
    SlurmState.REQUEUE_FED: SystemError,
    SlurmState.REQUEUE_HOLD: Held,
    SlurmState.RESV_DEL_HOLD: Held,
    SlurmState.REQUEUED: Pending,
    SlurmState.SUSPENDED: Paused,
    SlurmState.RESIZING: SystemError,
    SlurmState.REVOKED: SystemError,
    SlurmState.SPECIAL_EXIT: SystemError
})
