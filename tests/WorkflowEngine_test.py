#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from pathlib import Path

import pytest

from weskit import WorkflowEngineFactory
from weskit.classes.WorkflowEngine import Snakemake, Nextflow
from weskit.classes.WorkflowEngineParameters import \
    EngineParameter, ActualEngineParameter, ParameterIndex


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
        [{"name": "cores", "value": "2", "api": True},
         {"name": "use-singularity", "value": "TRUE", "api": True},
         {"name": "use-conda", "value": "TRUE", "api": True},
         {"name": "profile", "value": "TRUE", "api": True}]
    )
    assert engine.default_params == [
        ActualEngineParameter(EngineParameter({"cores"}), "2", True),
        ActualEngineParameter(EngineParameter({"use-singularity"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"use-conda"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"profile"}), "TRUE", True)
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
        [{"name": "cores", "value": "2", "api": True},
         {"name": "use-singularity", "value": "T", "api": True},
         {"name": "use-conda", "value": "T", "api": True},
         {"name": "profile", "value": "myprofile", "api": True}]
    )

    # Test default value with empty run parameters.
    command = engine.command(Path("/some/path"),
                             Path("/some/workdir"),
                             [Path("/some/config.yaml")],
                             {})
    assert command.command == ['snakemake',
                               '--snakefile', '/some/path',
                               '--cores', '2',
                               '--use-singularity',
                               '--use-conda',
                               '--profile', 'myprofile',
                               '--configfile', '/some/config.yaml']
    assert command.environment == {}
    assert command.workdir == Path("/some/workdir")


def test_command_with_run_parameter():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
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
    assert command.environment == {}
    assert command.workdir == Path("/a/workdir")


def test_command_with_unset_parameter():
    engine = WorkflowEngineFactory.create_engine(
        Snakemake,
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
    assert command.environment == {}
    assert command.workdir == Path("/a/workdir")


def test_command_setting_non_api_parameter():
    engine2 = WorkflowEngineFactory.create_engine(
        Snakemake,
        [{"name": "cores", "value": "2", "api": False},
         {"name": "use-singularity", "value": "T", "api": True},
         {"name": "use-conda", "value": "T", "api": True},
         {"name": "profile", "value": "myprofile", "api": True}]
    )
    with pytest.raises(KeyError):
        engine2.command(Path("/some/path"),
                        Path("/a/workdir"),
                        [Path("/the/config.file")],
                        {"cores": "1"})


def test_create_nextflow():
    engine = WorkflowEngineFactory.create_engine(
        Nextflow,
        # Note that different variants of `True` values are used.
        [{"name": "max-memory", "value": "2G", "api": False},
         {"name": "trace", "value": "TRUE", "api": True},
         {"name": "report", "value": "T", "api": True},
         {"name": "graph", "value": "Y", "api": True},
         {"name": "timeline", "value": "True", "api": True}]
    )
    assert engine.default_params == [
        ActualEngineParameter(EngineParameter({"max-memory"}), "2G", False),
        ActualEngineParameter(EngineParameter({"trace"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"report"}), "T", True),
        ActualEngineParameter(EngineParameter({"graph"}), "Y", True),
        ActualEngineParameter(EngineParameter({"timeline"}), "True", True)
    ]
    assert engine.name() == "NFL"

    created1 = engine.command(Path("/some/path"),
                              Path("/some/workdir"),
                              [Path("/some/config.yaml")],
                              {})
    assert created1.command == ['nextflow', "run", "/some/path",
                                '-params-file', '/some/config.yaml',
                                '-with-trace',
                                '-with-report',
                                '-with-dag',
                                '-with-timeline']
    assert created1.environment == {"NXF_OPTS": "-Xmx2048m"}
    assert created1.workdir == Path("/some/workdir")

    # Note that different variants of `False` are used and correctly interpreted.
    created2 = engine.command(Path("/some/path"),
                              Path("/a/workdir"),
                              [Path("/the/config.file")],
                              {"graph": "False",
                               "timeline": "F",
                               "report": "N",
                               "trace": "FALSE"})
    assert created2.command == ['nextflow', "run", "/some/path",
                                '-params-file', '/the/config.file']
    assert created2.environment == {"NXF_OPTS": "-Xmx2048m"}
    assert created2.workdir == Path("/a/workdir")

    with pytest.raises(KeyError):
        engine.command(Path("/some/path"),
                       Path("/a/workdir"),
                       [Path("/the/config.file")],
                       {"max-memory": "256m"})


def test_create_engines():
    engines = WorkflowEngineFactory.create({
        "NFL": {"vers1": [{"name": "max-memory", "value": "50gb"}]},
        "SMK": {"vers2": [{"name": "cores", "value": "100"}]}
    })

    assert engines["NFL"]["vers1"].name() == "NFL"
    assert engines["NFL"]["vers1"].default_params == [
        ActualEngineParameter(Nextflow.known_parameters()["max-memory"], "50gb")]
    assert engines["SMK"]["vers2"].name() == "SMK"
    assert engines["SMK"]["vers2"].default_params == [
        ActualEngineParameter(Snakemake.known_parameters()["cores"], "100")
    ]
