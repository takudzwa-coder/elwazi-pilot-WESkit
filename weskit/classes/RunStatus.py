#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations
import enum
from typing import List, Optional


class RunStatus(enum.Enum):
    """
    WES API run states.
    """

    # QUEUED: The task is queued.
    #
    # WESkit: A task is queued as soon as some Celery task is submitted for it and in
    #         Celery:PENDING state. This may be a run-task representing a workflow engine run
    #         (INITIALIZING -> QUEUE -> RUNNING), but may also include a preparatory task to stage
    #         large request-attachments, etc. (QUEUE -> INITIALIZING -> RUNNING).
    QUEUED = 1

    # > INITIALIZING: The task has been assigned to a worker and is currently preparing to run.
    #                 For example, the worker may be turning on, downloading input files, etc.
    #
    # WESkit: The initialization of the actual workflow engine execution takes place. This may
    #         include final upload of large attachments, directory creation, etc. Also, if data
    #         need to be pre-staged in the run environment (e.g. downloaded from object storage
    #         this is part of the INITIALIZING state.
    INITIALIZING = 2

    # > RUNNING: The task is running. Input files are downloaded and the first Executor
    #            has been started.
    #
    # WESkit: An "Executor" seems to be executing individual workfload jobs ("first Executor", etc.)
    #         WESkit has no access to these Executors, which are managed by the workflow engines.
    #         Thus, the RUNNING state is assumed, as long as the workflow engine runs.
    RUNNING = 3

    # > PAUSED: The task is paused.
    #           An implementation may have the ability to pause a task, but this is not required.
    #
    # WESkit: Not supported yet.
    PAUSED = 4

    # > COMPLETE: The task has completed running. Executors have exited without error
    # and output files have been successfully uploaded.
    #
    # WESkit: All workload jobs and the workflow engine executed with exit code == 0.
    COMPLETE = 5

    # > EXECUTOR_ERROR: The task encountered an error in one of the Executor processes. Generally,
    #                   this means that an Executor exited with a non-zero exit code.
    #
    # WESKIT: The "task" corresponds to a worklow engine execution. The workflow executes workload
    # jobs that correspond to the "Executors". The workflows, however, contain also code that is
    # executed by the workflow engine directly (which is an implementation detail of the engine).
    # Therefore, any error during the workflow processing by the engine -- be it in the core
    # workflow or in any of its workload jobs -- should map to EXECUTOR_ENGINE. E.g.
    #
    # * validation error of the config.yaml
    # * parameter validation/processing error in the workflow code
    # * errors during the execution of the workload (e.g. on the cluster).
    #
    # This means, the EXECUTOR_ERROR usually is used, if the workflow engine exited with code > 0.
    EXECUTOR_ERROR = 6

    # > SYSTEM_ERROR: The task was stopped due to a system error, but not from an Executor,
    #                 for example an upload failed due to network issues, the worker's ran out
    #                 of disk space, etc.
    #
    # WESkit: Any error of the WESkit system itself. Examples are
    #
    # * Celery worker error
    # * Errors in infrastructure (DB, Redis, Keycloak, etc.)
    # * Filesystem errors (inaccessible mounts, etc.), other than client-caused file access errors
    #   (e.g. wrong paths).
    # * WESkit.Executor errors (cluster errors, SSH errors, etc.)
    SYSTEM_ERROR = 7

    # > CANCELED: The task was canceled by the user.
    #
    # WESkit: The workflow engine run (~ task) has been successfully cancelled.
    CANCELED = 8

    # > CANCELING: The task was canceled by the user, and is in the process of stopping.
    #
    # WESkit: The workflow engine run (~ task) is being cancelled, e.g. waiting for the engine
    #         to respond to SIGTERM and clean up running cluster jobs, compiling incomplete run
    #         run results, etc.
    CANCELING = 9

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_string(name: str) -> RunStatus:
        return RunStatus[name]

    @staticmethod
    def from_celery_and_exit(celery_state_name: str, exit_code: Optional[int]) -> RunStatus:
        celery_to_wes_state = {
            "PENDING": RunStatus.QUEUED,
            "STARTED": RunStatus.RUNNING,
            "SUCCESS": RunStatus.COMPLETE,
            "FAILURE": RunStatus.SYSTEM_ERROR,
            "RETRY": RunStatus.QUEUED,
            "REVOKED": RunStatus.CANCELED
        }
        if celery_state_name == "SUCCESS":
            if exit_code is None:
                raise RuntimeError("Oops! Celery state SUCCESS but no exit code")
            elif exit_code > 0:
                return RunStatus.EXECUTOR_ERROR
            elif exit_code < 0:  # System error in task not resulting in Celery task FAILURE
                return RunStatus.SYSTEM_ERROR
            else:
                return celery_to_wes_state["SUCCESS"]
        else:
            return celery_to_wes_state[celery_state_name]

    @staticmethod
    def RUNNING_STATES() -> List[RunStatus]:
        return [RunStatus.QUEUED,
                RunStatus.RUNNING]

    @property
    def is_running(self) -> bool:
        return self in self.RUNNING_STATES()

    @staticmethod
    def TERMINAL_STATES() -> List[RunStatus]:
        return [RunStatus.COMPLETE,
                RunStatus.SYSTEM_ERROR,
                RunStatus.EXECUTOR_ERROR,
                RunStatus.CANCELED]

    @property
    def is_terminal(self) -> bool:
        return self in self.TERMINAL_STATES()

    @property
    def precedence(self) -> int:
        # Get the precedence of the state. This is analogous to Celery's precedence
        # (https://docs.celeryq.dev/en/stable/_modules/celery/states.html#precedence), but modified
        # and extended to WESkit's needs. It is used so simplify the decision-making for
        # concurrent modifications, but one should be aware that Celery seems not to make any
        # promises about the logical order of states. It cannot be ruled out that it is possible
        # that Celery could go from SUCCESS to CANCELED.
        PRECEDENCE = {
            RunStatus.INITIALIZING: 1,
            RunStatus.QUEUED: 2,
            RunStatus.RUNNING: 3,
            RunStatus.PAUSED: 4,
            RunStatus.CANCELING: 5,
            # The following are terminal states and not updated in the DB (see update_runs)
            RunStatus.CANCELED: 6,
            RunStatus.EXECUTOR_ERROR: 7,
            RunStatus.COMPLETE: 8,
            RunStatus.SYSTEM_ERROR: 9
        }
        return PRECEDENCE[self]

    @property
    def is_pausible(self) -> bool:
        return self in [RunStatus.RUNNING, RunStatus.QUEUED]

    def allowed_to_progress_to(self, new_state: RunStatus) -> bool:
        if self == new_state:
            # Obviously, keeping the state is allowed.
            return True
        elif new_state == RunStatus.SYSTEM_ERROR:
            # Transition to SYSTEM_ERROR is always allowed, however, this is irreversible.
            return True
        elif new_state == RunStatus.INITIALIZING:  # states are different
            # Currently, INITIALIZING is done in the flask thread and cannot be
            # reached after it was (successfully or not) terminated. Therefore ...
            return False
        elif (self.is_pausible and new_state == RunStatus.PAUSED) or \
                (self == RunStatus.PAUSED and new_state.is_pausible):
            # Transition to and from PAUSED is possible for "pausible" states. Note that it may be
            # possible to go via PAUSED to a state with lower precedence then the old state. The
            # sequence RUNNING -> PAUSED -> QUEUED is allowed.
            return True
        elif self == RunStatus.RUNNING and new_state == RunStatus.QUEUED:
            # This reflects Celery's RETRY and is allowed.
            return True
        elif self.precedence < new_state.precedence:
            # State changes along the precedence are allowed, unless a terminal state was already
            # reached before.
            return not self.is_terminal
        else:
            return False

    def progress_to(self, new_state: RunStatus) -> RunStatus:
        """
        Enforce state changes to be along allowed edges of the state graph.
        Raises a RuntimeError, if a forbidden state change is requested.

        NOTE: Currently, no check is done of the sequence of states. Only the current and new
              state are considered. Therefore, sequences going via the reversible states
              PAUSED and QUEUED (retry!) can be invalid but still be accepted here.

              E.g. CANCELING -> PAUSED -> RUNNING
        """
        if self.allowed_to_progress_to(new_state):
            return new_state
        else:
            raise RuntimeError(
                f"Forbidden state-change requested: '{self.name}' -/-> '{new_state.name}'")
