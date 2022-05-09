#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations
import enum


class RunStatus(enum.Enum):
    UNKNOWN = 0
    QUEUED = 1
    INITIALIZING = 2
    RUNNING = 3
    PAUSED = 4
    COMPLETE = 5

    # Executors are the workflow-engine runs and executor errors are the situations where the
    # workflow engine returns != 0. These are usually due to misconfiguration of the workflow
    # (e.g. via the config.json submitted with the RunRequest; request validation errors).
    # These errors can be frequent, dependent on the input of the WES client, such that it makes
    # sense to report them to the client, because the client can fix them.
    EXECUTOR_ERROR = 6

    # System errors are more severe errors of the WESkit system. This includes all infrastructure
    # problems, such as access denied to filesystem, submission failed because of cluster issues
    # (e.g. server not responding, wrong password). This also includes runtime errors that represent
    # programming bugs in WESkit. These errors should be rare. They must be documented in the logs,
    # but may also be interesting for the client (to tell it, that there is a serious problem).
    # Note that client-visible error messages must not expose sensitive configuration information of
    # the WESkit server.
    SYSTEM_ERROR = 7

    CANCELED = 8
    CANCELING = 9

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_string(name: str) -> RunStatus:
        return RunStatus[name]
