# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import pytest

from weskit.api.RunStatus import RunStatus
from weskit.classes.ProcessingStage import ProcessingStage


def test_runstatus_from_processingstage():
    assert RunStatus.from_stage(ProcessingStage.AWAITING_START) == \
        RunStatus.INITIALIZING
    assert RunStatus.from_stage(ProcessingStage.STARTED_EXECUTION) == \
        RunStatus.RUNNING
    assert RunStatus.from_stage(ProcessingStage.FINISHED_EXECUTION) == \
        RunStatus.COMPLETE
    assert RunStatus.from_stage(ProcessingStage.SYSTEM_ERROR) == \
        RunStatus.SYSTEM_ERROR
    assert RunStatus.from_stage(ProcessingStage.EXECUTOR_ERROR) == \
        RunStatus.EXECUTOR_ERROR
    assert RunStatus.from_stage(ProcessingStage.CANCELED) == \
        RunStatus.CANCELED
    with pytest.raises(AttributeError):
        RunStatus.from_stage(ProcessingStage.NONEXISTING)


def test_from_string():
    assert ProcessingStage.from_string("SYSTEM_ERROR") == ProcessingStage.SYSTEM_ERROR
    assert ProcessingStage.from_string("AWAITING_START") == ProcessingStage.AWAITING_START
    assert ProcessingStage.from_string("blah") == ProcessingStage.SYSTEM_ERROR
