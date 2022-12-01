#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import pytest

from weskit.api.RunStatus import RunStatus
from weskit.classes.ProcessingStage import ProcessingStage


def test_runstatus_progress_state():
    assert RunStatus.from_stage(ProcessingStage.AWAITING_START) == RunStatus.INITIALIZING
    assert RunStatus.from_stage(ProcessingStage.STARTED_EXECUTION) == RunStatus.RUNNING
    assert RunStatus.from_stage(ProcessingStage.FINISHED_EXECUTION) == RunStatus.COMPLETE
    assert RunStatus.from_stage(ProcessingStage.ERROR) == RunStatus.SYSTEM_ERROR
    assert RunStatus.from_stage(ProcessingStage.EXECUTOR_ERROR) == RunStatus.EXECUTOR_ERROR
    assert RunStatus.from_stage(ProcessingStage.CANCELED) == RunStatus.CANCELED
    with pytest.raises(AttributeError):
        RunStatus.from_stage(ProcessingStage.NONEXISTING)
