#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations
import enum
from typing import Optional

from weskit.classes.ProcessingStage import ProcessingStage


class RunStatus(enum.Enum):
    """
    GA4GH run states.
    """

    # QUEUED: The task is queued.
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
    RUNNING = 3

    # > PAUSED: The task is paused.
    #           An implementation may have the ability to pause a task, but this is not required.
    PAUSED = 4

    # > COMPLETE: The task has completed running. Executors have exited without error
    #             and output files have been successfully uploaded.
    COMPLETE = 5

    # > EXECUTOR_ERROR: The task encountered an error in one of the Executor processes. Generally,
    #                   this means that an Executor exited with a non-zero exit code.
    EXECUTOR_ERROR = 6

    # > SYSTEM_ERROR: The task was stopped due to a system error, but not from an Executor,
    #                 for example an upload failed due to network issues, the worker's ran out
    #                 of disk space, etc.
    SYSTEM_ERROR = 7

    # > CANCELED: The task was canceled by the user.
    #
    CANCELED = 8

    # > CANCELING: The task was canceled by the user, and is in the process of stopping.
    #
    CANCELING = 9

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_stage(stage: ProcessingStage, exit_code: Optional[int]) -> RunStatus:
        weskit_stage_to_status = {
                                    ProcessingStage.RUN_CREATED: RunStatus.INITIALIZING,
                                    ProcessingStage.PREPARED_EXECUTION: RunStatus.INITIALIZING,
                                    ProcessingStage.SUBMITTED_EXECUTION: RunStatus.INITIALIZING,
                                    ProcessingStage.AWAITING_START: RunStatus.INITIALIZING,
                                    ProcessingStage.STARTED_EXECUTION: RunStatus.RUNNING,
                                    ProcessingStage.PAUSED: RunStatus.PAUSED,
                                    ProcessingStage.FINISHED_EXECUTION: RunStatus.COMPLETE,
                                    ProcessingStage.ERROR: RunStatus.SYSTEM_ERROR,
                                    ProcessingStage.CANCELED: RunStatus.CANCELED,
                                    ProcessingStage.REQUESTED_CANCEL: RunStatus.CANCELING
        }
        if stage == ProcessingStage.FINISHED_EXECUTION:
            if exit_code is None:
                # The exit_code returned from the worker should always be an integer, if the
                # Celery worker gets into the SUCCESS state.
                return RunStatus.SYSTEM_ERROR
            elif exit_code > 0:
                return RunStatus.EXECUTOR_ERROR
            elif exit_code < 0:  # System error in task not resulting in Celery task FAILURE
                return RunStatus.SYSTEM_ERROR
            else:
                return weskit_stage_to_status[ProcessingStage.FINISHED_EXECUTION]

        return weskit_stage_to_status[stage]
