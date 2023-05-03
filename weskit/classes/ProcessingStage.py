#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations
import enum
from typing import Optional, List


class ProcessingStage(enum.Enum):
    """
    WESkit system run states.
    """
    # > RUN_CREATED: Run was created. Maybe there is a directory, and maybe the attachment files
    #            were partially written to the run-dir.
    RUN_CREATED = 1

    # > PREPARED_EXECUTION: A Celery task ID was defined and the execution may or
    #                       may not have started.
    PREPARED_EXECUTION = 2

    # > SUBMITTED_EXECUTION: The execution of the workflow engine execution has been submitted
    #                        to the Celery task with the known ID.
    SUBMITTED_EXECUTION = 3

    # > AWAITING_START: Celery task is submitted. This may be a run-task representing a
    #                   workflow engine run but may also include a preparatory task to stage
    #                   large request-attachments, etc.
    AWAITING_START = 4

    # > STARTED_EXECUTION: An "Executor" seems to be executing individual
    #                      workfload jobs ("first Executor", etc.) WESkit has no access to
    #                      these Executors, which are managed by the workflow engines.
    #                      Thus, the RUNNING state is assumed, as long as the workflow engine runs.
    STARTED_EXECUTION = 5

    # > PAUSED: The workflow run is paused.
    #           Not implemented yet
    PAUSED = 6

    # > FINISHED: The Celery task finished (successfully or not).
    #             All workload jobs and the workflow engine executed with exit code == 0.
    FINISHED_EXECUTION = 7

    # > SYSTEM_ERROR: Any error of the WESkit system itself. Examples are
    #
    # * System error in task not resulting in Celery task FAILURE
    # * Errors in infrastructure (DB, Redis, Keycloak, etc.)
    # * Filesystem errors (inaccessible mounts, etc.), other than client-caused file access errors
    #   (e.g. wrong paths).
    # * WESkit.Executor errors (cluster errors, SSH errors, etc.)
    SYSTEM_ERROR = 8

    # > EXECUTOR_ERROR: The task encountered an error in one of the Executor processes.
    #   Generally, this means that an Executor exited with a non-zero exit code.
    #   exit_code > 0
    EXECUTOR_ERROR = 9

    # > CANCELED: The workflow engine run (~ task) has been successfully cancelled.
    #
    CANCELED = 10

    # > REQUESTED_CANCEL:  The workflow engine run (~ task) is being cancelled, e.g. waiting for the
    #               engine to respond to SIGTERM and clean up running cluster jobs,
    #               compiling incomplete run, run results, etc.
    REQUESTED_CANCEL = 11

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_string(name: str) -> ProcessingStage:
        return ProcessingStage[name]

    @staticmethod
    def from_celery_and_exit_code(celery_state_name: Optional[str],
                                  command_exit_code: Optional[int]) -> ProcessingStage:
        if celery_state_name is None:
            raise RuntimeError("run.celery_task_state should be set at this point")
        celery_to_weskit_stage = {
            "PENDING": ProcessingStage.AWAITING_START,
            "STARTED": ProcessingStage.STARTED_EXECUTION,
            "SUCCESS": ProcessingStage.FINISHED_EXECUTION,
            "RETRY": ProcessingStage.SYSTEM_ERROR,
            "REVOKED": ProcessingStage.CANCELED,
            "FAILURE": ProcessingStage.SYSTEM_ERROR
        }

        if celery_state_name == "SUCCESS":
            if command_exit_code is None:
                # The exit_code returned from the worker should always be an integer, if the
                # Celery worker gets into the SUCCESS state.
                return ProcessingStage.SYSTEM_ERROR
            elif command_exit_code > 0:
                return ProcessingStage.EXECUTOR_ERROR
            elif command_exit_code < 0:  # System error in task not resulting in Celery task FAILURE
                return ProcessingStage.SYSTEM_ERROR
            else:
                return celery_to_weskit_stage["SUCCESS"]

        return celery_to_weskit_stage[celery_state_name]

    @staticmethod
    def INITIALIZING_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.RUN_CREATED,
                ProcessingStage.PREPARED_EXECUTION,
                ProcessingStage.SUBMITTED_EXECUTION,
                ProcessingStage.AWAITING_START]

    @property
    def is_initializing(self) -> bool:
        return self in self.INITIALIZING_STAGES()

    @staticmethod
    def RUNNING_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.STARTED_EXECUTION]

    @property
    def is_running(self) -> bool:
        return self in self.RUNNING_STAGES()

    @staticmethod
    def TERMINAL_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.FINISHED_EXECUTION,
                ProcessingStage.SYSTEM_ERROR,
                ProcessingStage.EXECUTOR_ERROR,
                ProcessingStage.CANCELED]

    @property
    def is_terminal(self) -> bool:
        return self in self.TERMINAL_STAGES()

    @staticmethod
    def ERROR_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.SYSTEM_ERROR,
                ProcessingStage.EXECUTOR_ERROR]

    @property
    def is_error(self) -> bool:
        return self in self.ERROR_STAGES()

    @property
    def precedence(self) -> int:
        # Get the precedence of the state. This is analogous to Celery's precedence
        # (https://docs.celeryq.dev/en/stable/_modules/celery/states.html#precedence), but modified
        # and extended to WESkit's needs. It is used so simplify the decision-making for
        # concurrent modifications, but one should be aware that Celery seems not to make any
        # promises about the logical order of states. It cannot be ruled out that it is possible
        # that Celery could go from SUCCESS to CANCELED.
        PRECEDENCE = {
            ProcessingStage.RUN_CREATED: 1,
            ProcessingStage.PREPARED_EXECUTION: 2,
            ProcessingStage.SUBMITTED_EXECUTION: 3,
            ProcessingStage.AWAITING_START: 4,
            ProcessingStage.STARTED_EXECUTION: 5,
            ProcessingStage.PAUSED: 6,
            ProcessingStage.FINISHED_EXECUTION: 7,
            ProcessingStage.SYSTEM_ERROR: 8,
            ProcessingStage.EXECUTOR_ERROR: 9,
            ProcessingStage.CANCELED: 10,
            ProcessingStage.REQUESTED_CANCEL: 11
        }
        return PRECEDENCE[self]

    @property
    def is_pausible(self) -> bool:
        return self in [ProcessingStage.SUBMITTED_EXECUTION, ProcessingStage.AWAITING_START]

    def allowed_to_progress_to(self, new_state: ProcessingStage) -> bool:
        if self == new_state:
            # Obviously, keeping the state is allowed.
            return True
        elif not self.is_error and new_state.is_error:
            # Transition to ERROR is always allowed.
            return True
        elif (self.is_pausible and new_state == ProcessingStage.PAUSED) or \
                (self == ProcessingStage.PAUSED and new_state.is_pausible):
            return True
        elif self == ProcessingStage.CANCELED and \
                new_state == ProcessingStage.SUBMITTED_EXECUTION:
            # This reflects Celery's RETRY and is allowed.
            return True
        elif self.precedence < new_state.precedence:
            # Stage changes along the precedence are allowed, unless a terminal state was already
            # reached before.
            return not self.is_terminal
        else:
            return False

    def progress_to(self, new_state: ProcessingStage) -> ProcessingStage:
        """
        Enforce stage changes to be along allowed edges of the state graph.
        Raises a RuntimeError, if a forbidden state change is requested.

        NOTE: Currently, no check is done of the sequence of stages. Only the current and new
              stage are considered. Therefore, sequences going via the reversible states
              PAUSED and AWAITING_START (retry!) can be invalid but still be accepted here.

              E.g. REQUESTED_CANCEL -> PAUSED -> STARTED_EXECUTION
        """
        if self.allowed_to_progress_to(new_state):
            return new_state
        else:
            raise RuntimeError(
                f"Forbidden state-change requested: '{self.name}' -/-> '{new_state.name}'")
