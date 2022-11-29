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

    # > PREPARED_DIR: The attachment files have been written to the run-dir,
    #                 but no Celery task ID has yet been defined.
    PREPARED_DIR = 2

    # > PREPARED_EXECUTION: A Celery task ID was defined and the execution may or
    #                       may not have started.
    PREPARED_EXECUTION = 3

    # > SUBMITTED_EXECUTION: The execution of the workflow engine execution has been submitted
    #                        to the Celery task with the known ID.
    SUBMITTED_EXECUTION = 4

    # > AWAITING_START: Celery task is submitted. This may be a run-task representing a
    #                   workflow engine run but may also include a preparatory task to stage
    #                   large request-attachments, etc.
    AWAITING_START = 5

    # > STARTED_EXECUTION: An "Executor" seems to be executing individual
    #                      workfload jobs ("first Executor", etc.) WESkit has no access to
    #                      these Executors, which are managed by the workflow engines.
    #                      Thus, the RUNNING state is assumed, as long as the workflow engine runs.
    STARTED_EXECUTION = 6

    # > RERUN_EXECUTION: A Celery task is being retried.
    #
    RERUN_EXECUTION = 7

    # > PAUSED: The workflow run is paused.
    #           Not implemented yet
    PAUSED = 8

    # > FINISHED: The Celery task finished (successfully or not).
    #             All workload jobs and the workflow engine executed with exit code == 0.
    FINISHED_EXECUTION = 9

    # > ERROR: Any error of the WESkit system itself. Examples are
    #
    # * Celery worker error
    # * Errors in infrastructure (DB, Redis, Keycloak, etc.)
    # * Filesystem errors (inaccessible mounts, etc.), other than client-caused file access errors
    #   (e.g. wrong paths).
    # * WESkit.Executor errors (cluster errors, SSH errors, etc.)
    ERROR = 10

    # > EXECUTOR_ERROR: The "task" corresponds to a worklow engine execution. The workflow
    #                   executes workload jobs that correspond to the "Executors".
    #                   The workflows, however, contain also code that is executed by the workflow
    #                   engine directly (which is an implementation detail of the engine).
    #                   Therefore, any error during the workflow processing by the engine
    #                   -- be it in the coreworkflow or in any of its workload jobs --
    #                   should map to EXECUTOR_ENGINE.
    # E.g.
    # * validation error of the config.yaml
    # * parameter validation/processing error in the workflow code
    # * errors during the execution of the workload (e.g. on the cluster).
    #
    # This means, the EXECUTOR_ERROR usually is used, if the workflow engine exited with code > 0.
    EXECUTOR_ERROR = 11

    # > CANCELED: The workflow engine run (~ task) has been successfully cancelled.
    #
    CANCELED = 12

    # > REQUESTED_CANCEL:  The workflow engine run (~ task) is being cancelled, e.g. waiting for the
    #               engine to respond to SIGTERM and clean up running cluster jobs,
    #               compiling incomplete run, run results, etc.
    REQUESTED_CANCEL = 13

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_string(name: str) -> ProcessingStage:
        return ProcessingStage[name]

    @staticmethod
    def from_celery_and_exit(celery_state_name: Optional[str], exit_code: Optional[int]) -> \
            ProcessingStage:
        if celery_state_name is None:
            raise RuntimeError("run.celery_task_state should be set at this point")
        celery_to_weskit_stage = {
            "PENDING": ProcessingStage.AWAITING_START,
            "STARTED": ProcessingStage.STARTED_EXECUTION,
            "SUCCESS": ProcessingStage.FINISHED_EXECUTION,
            "RETRY": ProcessingStage.RERUN_EXECUTION,
            "REVOKED": ProcessingStage.CANCELED,
            "FAILURE": ProcessingStage.ERROR
        }
        if celery_state_name == "SUCCESS":
            if exit_code is None:
                # The exit_code returned from the worker should always be an integer, if the
                # Celery worker gets into the SUCCESS state.
                return ProcessingStage.ERROR
            elif exit_code > 0:
                return ProcessingStage.EXECUTOR_ERROR
            elif exit_code < 0:  # System error in task not resulting in Celery task FAILURE
                return ProcessingStage.ERROR
            else:
                return celery_to_weskit_stage["SUCCESS"]
        else:
            return celery_to_weskit_stage[celery_state_name]

    @staticmethod
    def INITIALIZING_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.RUN_CREATED,
                ProcessingStage.PREPARED_DIR,
                ProcessingStage.PREPARED_EXECUTION,
                ProcessingStage.SUBMITTED_EXECUTION,
                ProcessingStage.AWAITING_START]

    @property
    def is_initializing(self) -> bool:
        return self in self.INITIALIZING_STAGES()

    @staticmethod
    def RUNNING_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.STARTED_EXECUTION,
                ProcessingStage.RERUN_EXECUTION]

    @property
    def is_running(self) -> bool:
        return self in self.RUNNING_STAGES()

    @staticmethod
    def TERMINAL_STAGES() -> List[ProcessingStage]:
        return [ProcessingStage.FINISHED_EXECUTION,
                ProcessingStage.ERROR,
                ProcessingStage.EXECUTOR_ERROR,
                ProcessingStage.CANCELED]

    @property
    def is_terminal(self) -> bool:
        return self in self.TERMINAL_STAGES()

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
            ProcessingStage.PREPARED_DIR: 2,
            ProcessingStage.PREPARED_EXECUTION: 3,
            ProcessingStage.SUBMITTED_EXECUTION: 4,
            ProcessingStage.AWAITING_START: 5,
            ProcessingStage.STARTED_EXECUTION: 6,
            ProcessingStage.RERUN_EXECUTION: 7,
            ProcessingStage.PAUSED: 8,
            ProcessingStage.FINISHED_EXECUTION: 9,
            ProcessingStage.ERROR: 10,
            ProcessingStage.EXECUTOR_ERROR: 11,
            ProcessingStage.CANCELED: 12,
            ProcessingStage.REQUESTED_CANCEL: 13
        }
        return PRECEDENCE[self]

    @property
    def is_pausible(self) -> bool:
        return self in [ProcessingStage.SUBMITTED_EXECUTION, ProcessingStage.AWAITING_START]

    def allowed_to_progress_to(self, new_state: ProcessingStage) -> bool:
        if self == new_state:
            # Obviously, keeping the state is allowed.
            return True
        elif self != ProcessingStage.ERROR and new_state == ProcessingStage.ERROR:
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
            return self not in [ProcessingStage.FINISHED_EXECUTION, ProcessingStage.ERROR]
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
