#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from weskit.tasks.EngineExecutor import EngineExecutorType


def test_engine_executor_type_construction():
    assert EngineExecutorType.from_string("local") == EngineExecutorType.LOCAL
    assert EngineExecutorType.from_string("local_LSF") == EngineExecutorType.LOCAL_LSF
    assert EngineExecutorType.from_string("SSH_SLURM") == EngineExecutorType.SSH_SLURM
    assert EngineExecutorType.from_string("ssh_slurm") == EngineExecutorType.SSH_SLURM


def test_engine_executor_type_needs_login():
    assert EngineExecutorType.SSH.needs_login_credentials
    assert EngineExecutorType.SSH_SLURM.needs_login_credentials
    assert EngineExecutorType.SSH_LSF.needs_login_credentials

    assert not EngineExecutorType.LOCAL.needs_login_credentials
    assert not EngineExecutorType.LOCAL_LSF.needs_login_credentials
    assert not EngineExecutorType.LOCAL_SLURM.needs_login_credentials


def test_engine_executor_type_remote():
    assert not EngineExecutorType.LOCAL.executes_engine_remotely

    assert EngineExecutorType.LOCAL_LSF.executes_engine_remotely
    assert EngineExecutorType.LOCAL_SLURM.executes_engine_remotely

    assert EngineExecutorType.SSH.executes_engine_remotely
    assert EngineExecutorType.SSH_SLURM.executes_engine_remotely
    assert EngineExecutorType.SSH_LSF.executes_engine_remotely
