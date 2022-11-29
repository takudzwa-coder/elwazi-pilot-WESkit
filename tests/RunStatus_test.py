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
    assert RunStatus.ga4gh_state("AWAITING_START") == RunStatus.INITIALIZING
    assert RunStatus.ga4gh_state(ProcessingStage.AWAITING_START) == RunStatus.INITIALIZING
    assert RunStatus.ga4gh_state("STARTED_EXECUTION") == RunStatus.RUNNING
    assert RunStatus.ga4gh_state("FINISHED_EXECUTION") == RunStatus.COMPLETE
    assert RunStatus.ga4gh_state("ERROR") == RunStatus.SYSTEM_ERROR
    assert RunStatus.ga4gh_state("EXECUTOR_ERROR") == RunStatus.EXECUTOR_ERROR
    assert RunStatus.ga4gh_state("RERUN_EXECUTION") == RunStatus.QUEUED
    assert RunStatus.ga4gh_state("CANCELED") == RunStatus.CANCELED
    with pytest.raises(KeyError):
        RunStatus.ga4gh_state("NONEXISTING")
