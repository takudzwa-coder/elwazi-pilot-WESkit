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
    EXECUTOR_ERROR = 6
    SYSTEM_ERROR = 7
    CANCELED = 8
    CANCELING = 9

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def from_string(name: str) -> RunStatus:
        return RunStatus[name]
