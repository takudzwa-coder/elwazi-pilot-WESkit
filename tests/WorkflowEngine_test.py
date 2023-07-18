#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from datetime import timedelta
from pathlib import Path

import pytest

from weskit.classes.ShellCommand import ss
from weskit import WorkflowEngineFactory
from weskit.classes.WorkflowEngine import Snakemake, Nextflow
from weskit.classes.WorkflowEngineParameters import \
    EngineParameter, ActualEngineParameter, ParameterIndex
from weskit.exceptions import ClientError
from weskit.memory_units import Memory, Unit


def test_engine_parameter():
    a1 = EngineParameter({"a"})
    a2 = EngineParameter({"a"})
    b = EngineParameter({"b"})
    assert a1 == a2
    assert a1 != b

    assert a1.__hash__() == a2.__hash__()


def test_engine_parameter_index():
    p1 = EngineParameter({"a", "b"})
    p2 = EngineParameter({"a", "c"})
    p3 = EngineParameter({"c", "d"})

    idx = ParameterIndex([p1, p3])
    assert idx.all == [p1, p3]
    assert idx.get("a") == p1
    assert idx["b"] == p1
    assert idx["c"] == p3
    assert idx["d"] == p3

    with pytest.raises(ValueError):
        ParameterIndex([p1, p2])

    with pytest.raises(ValueError):
        ParameterIndex([p2, p3])

    assert idx.subset(frozenset({"a", "b"})).all == [p1]
    assert idx.subset(frozenset({"a", "c"})).all == [p1, p3]


def test_actual_parameter():
    param = EngineParameter({"a"})
    a1 = ActualEngineParameter(param, "1")
    assert a1.param == param
    assert a1.value == "1"

    a2 = ActualEngineParameter(param, "2")
    assert a1 != a2

    a3 = ActualEngineParameter(param, "1")
    assert a1 == a3


def test_create_snakemake():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "cores", "value": "2", "api": True},
         {"name": "use-singularity", "value": "TRUE", "api": True},
         {"name": "use-conda", "value": "TRUE", "api": True},
         {"name": "profile", "value": "TRUE", "api": True},
         {"name": "tes", "value": "TRUE", "api": True}]
    )
    assert engine.default_params == [
        ActualEngineParameter(EngineParameter({"cores"}), "2", True),
        ActualEngineParameter(EngineParameter({"use-singularity"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"use-conda"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"profile"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"tes"}), "TRUE", True)
    ]
    assert engine.name() == "SMK"


# Command composition
# Note that ShellCommand is not immutable. It contains mutable collections (list, dict) from
# which it is not trivial to get immutable variants (tuple for List is easy, but namedtuple
# for Dict? Or frozendict package? -- native support for immutable types in Python is
# unsatisfactory). Therefore, for now we did not make ShellCommand immutable with __eq__ and
# __hash__ implementations.

def test_command_with_default_parameters():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "cores", "value": "2", "api": True},
         {"name": "use-singularity", "value": "T", "api": True},
         {"name": "use-conda", "value": "T", "api": True},
         {"name": "resume", "value": "T", "api": True},
         {"name": "profile", "value": "myprofile", "api": True},
         {"name": "tes", "value": "https://some/test/URL", "api": True},
         {"name": "jobs", "value": "1", "api": True},
         {"name": "data_aws_access_key_id", "value": "GyCCggXpRpKQ3hBB", "api": True},
         {"name": "data_aws_secret_access_key", "value": "basTuIRppYhACCdXS6yYZb1XhUTksJPq",
          "api": True},
         {"name": "task_conda_envs_path", "value": "some/relative/path/", "api": True},
         {"name": "task_home", "value": "/tmp", "api": True}
         ]
    )

    # Test default value with empty run parameters.
    command = engine.command(Path("/some/path"),
                             Path("/some/workdir"),
                             [Path("/some/config.yaml")],
                             {"data_aws_access_key_id": "GyCCggXpRpKQ3hBB",
                              "data_aws_secret_access_key": "basTuIRppYhACCdXS6yYZb1XhUTksJPq",
                              "task_conda_envs_path": "some/relative/path/",
                              "task_home": "/tmp"})
    assert command.command == ['snakemake',
                               '--snakefile', '/some/path',
                               '--cores', '2',
                               '--use-singularity',
                               '--use-conda',
                               '--profile', 'myprofile',
                               '--tes', 'https://some/test/URL',
                               '--jobs', '1',
                               '--configfile', '/some/config.yaml',
                               '--envvars', "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                               "CONDA_ENVS_PATH", "HOME"
                               ]

    assert command.environment == {
        'AWS_ACCESS_KEY_ID': 'GyCCggXpRpKQ3hBB',
        'AWS_SECRET_ACCESS_KEY': 'basTuIRppYhACCdXS6yYZb1XhUTksJPq',
        'CONDA_ENVS_PATH': 'some/relative/path/',
        'HOME': '/tmp',
        "WESKIT_WORKFLOW_ENGINE": "SMK=6.10.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert command.workdir == Path("/some/workdir")


def test_command_with_run_parameter():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "cores", "value": "2", "api": True}]
    )

    command = engine.command(Path("/some/path"),
                             Path("/a/workdir"),
                             [Path("/the/config.file")],
                             {"cores": "1"})
    assert command.command == ['snakemake',
                               '--snakefile', '/some/path',
                               '--cores', '1',
                               '--configfile', '/the/config.file']
    assert command.environment == {
        "WESKIT_WORKFLOW_ENGINE": "SMK=6.10.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert command.workdir == Path("/a/workdir")


def test_engine_execution_settings():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "job-name", "value": None, "api": True},
         {"name": "max-runtime", "value": "15:00", "api": True},
         {"name": "max-memory", "value": "5G", "api": True},
         {"name": "cores", "value": "2", "api": True},
         {"name": "group", "value": None, "api": True},
         {"name": "accounting-name", "value": None, "api": True},
         {"name": "queue", "value": None, "api": True},
         ]
    )

    default_settings = engine.execution_settings({})
    assert default_settings.job_name is None
    assert default_settings.walltime == timedelta(hours=15)
    assert default_settings.memory == Memory(value=5, unit=Unit.GIGA)
    assert default_settings.cores == 2
    assert default_settings.group is None
    assert default_settings.accounting_name is None
    assert default_settings.queue is None

    settings = engine.execution_settings({"job-name": "the-job",
                                          "max-runtime": "125:00",
                                          "max-memory": "2G",
                                          "cores": "4",
                                          "group": "groupX",
                                          "accounting-name": "projectX",
                                          "queue": "the-queue"})
    assert settings.job_name == "the-job"
    assert settings.walltime == timedelta(hours=125)
    assert settings.memory == Memory(value=2, unit=Unit.GIGA)
    assert settings.cores == 4
    assert settings.group == "groupX"
    assert settings.accounting_name == "projectX"
    assert settings.queue == "the-queue"


def test_forbidden_engine_execution_settings():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "job-name", "value": None, "api": False},
         {"name": "max-runtime", "value": "15:00", "api": True},
         {"name": "max-memory", "value": "5G", "api": True},
         {"name": "cores", "value": "2", "api": True},
         {"name": "group", "value": None, "api": True},
         {"name": "accounting-name", "value": None, "api": True},
         {"name": "queue", "value": None, "api": True},
         ]
    )

    with pytest.raises(ClientError):
        engine.execution_settings({"job-name": "the-job",
                                   "max-runtime": "125:00",
                                   "max-memory": "2G",
                                   "cores": "4",
                                   "group": "groupX",
                                   "accounting-name": "projectX",
                                   "queue": "the-queue"})


def test_command_with_unset_parameter():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "cores", "value": "2", "api": True}]
    )

    # Try unsetting value parameter.
    command = engine.command(Path("/some/path"),
                             Path("/a/workdir"),
                             [Path("/the/config.file")],
                             {"cores": None})
    assert command.command == ['snakemake',
                               '--snakefile', '/some/path',
                               '--configfile', '/the/config.file']
    assert command.environment == {
        "WESKIT_WORKFLOW_ENGINE": "SMK=6.10.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert command.workdir == Path("/a/workdir")


def test_command_setting_non_api_parameter():
    engine2 = WorkflowEngineFactory.create_engine(
        Snakemake,
        "6.10.0",
        [{"name": "engine-environment", "value": None, "api": False},  # test: accept None value
         {"name": "cores", "value": "2", "api": False},
         {"name": "use-singularity", "value": "T", "api": True},
         {"name": "use-conda", "value": "T", "api": True},
         {"name": "profile", "value": "myprofile", "api": True}]
    )
    with pytest.raises(ClientError):
        engine2.command(Path("/some/path"),
                        Path("/a/workdir"),
                        [Path("/the/config.file")],
                        {"cores": "1"})


def test_create_nextflow():
    engine = WorkflowEngineFactory.create_engine(
        Nextflow,
        "21.04.0",
        # Note that different variants of `True` values are used.
        [{"name": "engine-environment", "value": "/path/to/script", "api": False},
         {"name": "max-memory", "value": "2G", "api": False},
         {"name": "trace", "value": "TRUE", "api": True},
         {"name": "report", "value": "T", "api": True},
         {"name": "graph", "value": "Y", "api": True},
         {"name": "timeline", "value": "True", "api": True},
         {"name": "resume", "value": "True", "api": True}]
    )
    assert engine.default_params == [
        ActualEngineParameter(EngineParameter({"engine-environment"}), "/path/to/script", False),
        ActualEngineParameter(EngineParameter({"max-memory"}), "2G", False),
        ActualEngineParameter(EngineParameter({"trace"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"report"}), "T", True),
        ActualEngineParameter(EngineParameter({"graph"}), "Y", True),
        ActualEngineParameter(EngineParameter({"timeline"}), "True", True),
        ActualEngineParameter(EngineParameter({"resume"}), "True", True)
    ]
    assert engine.name() == "NFL"

    created1 = engine.command(Path("/some/path"),
                              Path("/some/workdir"),
                              [Path("/some/config.yaml")],
                              {})
    assert created1.command == ['set', '-eu', '-o', 'pipefail', ss('&&'),
                                'source', '/path/to/script', ss("&&"),
                                'nextflow', "run", "/some/path",
                                '-params-file', '/some/config.yaml',
                                '-with-trace',
                                '-with-report',
                                '-with-dag',
                                '-with-timeline',
                                '-resume']
    assert created1.environment == {
        "NXF_OPTS": "-Xmx2048m",
        "WESKIT_WORKFLOW_ENGINE": "NFL=21.04.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert created1.workdir == Path("/some/workdir")

    # Note that different variants of `False` are used and correctly interpreted.
    created2 = engine.command(Path("/some/path"),
                              Path("/a/workdir"),
                              [Path("/the/config.file")],
                              {"graph": "False",
                               "timeline": "F",
                               "report": "N",
                               "trace": "FALSE"})
    assert created2.command == ['set', '-eu', '-o', 'pipefail', ss('&&'),
                                'source', '/path/to/script', ss('&&'),
                                'nextflow', "run", "/some/path",
                                '-params-file', '/the/config.file',
                                '-resume']
    assert created2.environment == {
        "NXF_OPTS": "-Xmx2048m",
        "WESKIT_WORKFLOW_ENGINE": "NFL=21.04.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert created2.workdir == Path("/a/workdir")

    with pytest.raises(ClientError):
        engine.command(Path("/some/path"),
                       Path("/a/workdir"),
                       [Path("/the/config.file")],
                       {"max-memory": "256m"})


def test_create_engines():
    engines = WorkflowEngineFactory.create({
        "NFL": {"vers1": {"default_parameters": [{"name": "max-memory", "value": "50gb"}]}},
        "SMK": {"vers2": {"default_parameters": [{"name": "cores", "value": "100"}]}}
    })

    assert engines["NFL"]["vers1"].name() == "NFL"
    assert engines["NFL"]["vers1"].version == "vers1"
    assert engines["NFL"]["vers1"].default_params == [
        ActualEngineParameter(Nextflow.known_parameters()["max-memory"], "50gb")]
    assert engines["SMK"]["vers2"].name() == "SMK"
    assert engines["SMK"]["vers2"].version == "vers2"
    assert engines["SMK"]["vers2"].default_params == [
        ActualEngineParameter(Snakemake.known_parameters()["cores"], "100")
    ]
