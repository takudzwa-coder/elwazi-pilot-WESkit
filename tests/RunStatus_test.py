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


def test_runstatus_from_processingstage():
    assert RunStatus.from_stage(ProcessingStage.AWAITING_START, exit_code=None) == \
        RunStatus.INITIALIZING
    assert RunStatus.from_stage(ProcessingStage.STARTED_EXECUTION, exit_code=None) == \
        RunStatus.RUNNING
    assert RunStatus.from_stage(ProcessingStage.FINISHED_EXECUTION, exit_code=0) == \
        RunStatus.COMPLETE
    assert RunStatus.from_stage(ProcessingStage.ERROR, exit_code=None) == \
        RunStatus.SYSTEM_ERROR
    assert RunStatus.from_stage(ProcessingStage.CANCELED, exit_code=None) == \
        RunStatus.CANCELED
    with pytest.raises(AttributeError):
        RunStatus.from_stage(ProcessingStage.NONEXISTING, exit_code=None)
