#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import os
import textwrap
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from urllib3.util import Url

from serializer import encode_json, decode_json
from weskit.classes.RunMetadataCollector import RunMetadata
from classes.executor.cluster.os.LocalExecutor import LocalExecutor
from weskit.utils import now, format_timestamp
from weskit.classes.executor.Executor import CommandResult, ProcessId, ExecutionStatus
from weskit.classes.ShellCommand import ss, ShellCommand
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

    a1_dict = dict(a1)
    assert a1_dict == {
        "name": "a",
        "value": "1",
        "api_parameter": False
    }
    assert a1 == ActualEngineParameter.from_dict(a1_dict)

    # Test serialization
    a1_json = encode_json(a1)
    assert a1_json == {}

    assert a1 == decode_json(a1_json)


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
         {"name": "forceall", "value": "T", "api": True},
         {"name": "profile", "value": "myprofile", "api": True},
         {"name": "tes", "value": "https://some/test/URL", "api": True},
         {"name": "jobs", "value": "1", "api": True},
         {"name": "envvar_aws_access_key_id", "value": "AWS_ACCESS_KEY_ID", "api": True},
         {"name": "envvar_conda_envs_path", "value": "CONDA_ENVS_PATH", "api": True},
         {"name": "envvar_home", "value": "/tmp", "api": True},
         {"name": "prefix_conda_envs_path", "value": "$CONDA_ENVS_PATH", "api": True}
         ]
    )

    # Test default value with empty run parameters.
    command = engine.run_command(Path("/some/path"),
                                 Path("/some/workdir"),
                                 [Path("/some/config.yaml")],
                                 {"envvar_aws_access_key_id": "AWS_ACCESS_KEY_ID",
                              "envvar_conda_envs_path": "CONDA_ENVS_PATH",
                              "envvar_home": "/tmp",
                              "prefix_conda_envs_path": "$CONDA_ENVS_PATH"})
    assert command.command == ['snakemake',
                               '--snakefile', '/some/path',
                               '--cores', '2',
                               '--use-singularity',
                               '--use-conda',
                               '--forceall',
                               '--profile', 'myprofile',
                               '--tes', 'https://some/test/URL',
                               '--jobs', '1',
                               '--configfile', '/some/config.yaml',
                               '--envvars', 'AWS_ACCESS_KEY_ID CONDA_ENVS_PATH /tmp',
                               '--conda-prefix', '$CONDA_ENVS_PATH']
    assert command.environment == {
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

    command = engine.run_command(Path("/some/path"),
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
    command = engine.run_command(Path("/some/path"),
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
        engine2.run_command(Path("/some/path"),
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
         {"name": "timeline", "value": "True", "api": True}]
    )
    assert engine.default_params == [
        ActualEngineParameter(EngineParameter({"engine-environment"}), "/path/to/script", False),
        ActualEngineParameter(EngineParameter({"max-memory"}), "2G", False),
        ActualEngineParameter(EngineParameter({"trace"}), "TRUE", True),
        ActualEngineParameter(EngineParameter({"report"}), "T", True),
        ActualEngineParameter(EngineParameter({"graph"}), "Y", True),
        ActualEngineParameter(EngineParameter({"timeline"}), "True", True)
    ]
    assert engine.name() == "NFL"

    created1 = engine.run_command(Path("/some/path"),
                                  Path("/some/workdir"),
                                  [Path("/some/config.yaml")],
                                  {})
    assert created1.command == ['source', '/path/to/script', ss("&&"),
                                'set', '-eu', '-o', 'pipefail', ss('&&'),
                                'nextflow', "run", "/some/path",
                                '-params-file', '/some/config.yaml',
                                '-with-trace',
                                '-with-report',
                                '-with-dag',
                                '-with-timeline']
    assert created1.environment == {
        "NXF_OPTS": "-Xmx2048m",
        "WESKIT_WORKFLOW_ENGINE": "NFL=21.04.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert created1.workdir == Path("/some/workdir")

    # Note that different variants of `False` are used and correctly interpreted.
    created2 = engine.run_command(Path("/some/path"),
                                  Path("/a/workdir"),
                                  [Path("/the/config.file")],
                                  {"graph": "False",
                                   "timeline": "F",
                                   "report": "N",
                                   "trace": "FALSE"})
    assert created2.command == ['source', '/path/to/script', ss('&&'),
                                'set', '-eu', '-o', 'pipefail', ss('&&'),
                                'nextflow', "run", "/some/path",
                                '-params-file', '/the/config.file']
    assert created2.environment == {
        "NXF_OPTS": "-Xmx2048m",
        "WESKIT_WORKFLOW_ENGINE": "NFL=21.04.0",
        "WESKIT_WORKFLOW_PATH": "/some/path"
    }
    assert created2.workdir == Path("/a/workdir")

    with pytest.raises(ClientError):
        engine.run_command(Path("/some/path"),
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


def test_parse_snakemake_stdout():
    stdout = textwrap.dedent("""
    Building DAG of jobs...
    [TES] Job execution on TES: https://tesk-na.cloud.e-infra.cz
    Using shell: /usr/bin/bash
    Job stats:
    job           count    min threads    max threads
    ----------  -------  -------------  -------------
    all               1              1              1
    processing        1              1              1
    total             2              1              1

    Select jobs to execute...

    [Tue Nov  8 14:22:42 2022]
    rule processing:
        input: ahm2022/userName/indata.txt
        output: ahm2022/bio-hack-test/outfile.txt
        jobid: 1
        resources: tmpdir=/tmp

    Unable to retrieve additional files from git. This is not a git repository.
    {'path': '/tmp/Snakefile', 'url': None, 'content': 'from snakemake.remote.S3 import RemoteProvider as S3RemoteProviderimport uuidS3 = S3RemoteProvider(    endpoint_url="https://s3-elixir.cloud.e-infra.cz")outfile_s3 = "ahm2022/bio-hack-test/outfile.txt"rule all:    input:        file=S3.remote(outfile_s3)rule processing:    input:        file=S3.remote("ahm2022/userName/indata.txt")    output:        file=S3.remote(outfile_s3)    params:        text="test text blablablubb"    shell:        \"""        cp {input.file} {output.file}        echo \'' >> {output.file}        echo {params.text} >> {output.file}        \"""'}
    {'path': '/tmp/run_snakemake.sh', 'url': None, 'content': '#!/bin/sh# properties = {"type": "single", "rule": "processing", "local": false, "input": ["ahm2022/userName/indata.txt"], "output": ["ahm2022/bio-hack-test/outfile.txt"], "wildcards": {}, "params": {"text": "test text blablablubb"}, "log": [], "threads": 1, "resources": {"tmpdir": "/tmp"}, "jobid": 1, "cluster": {}}export AWS_ACCESS_KEY_ID=GyCCggXpRpKQ3hBB;export CONDA_ENVS_PATH=/tmp/conda;export CONDA_PKGS_DIRS=/tmp/conda;export AWS_SECRET_ACCESS_KEY=basTuIRppYhACCdXS6yYZb1XhUTksJPq;export HOME=/tmp; mkdir /tmp/conda && cd /tmp && snakemake ahm2022/bio-hack-test/outfile.txt --snakefile Snakefile --verbose --force --cores all --keep-target-files --keep-remote --latency-wait 10 --attempt 1 --force-use-threads --allowed-rules processing --nocolor --notemp --no-hooks --nolock --mode 2  --use-conda  --conda-frontend mamba  --conda-prefix /tmp/conda  --local-groupid 1  --default-resources "tmpdir=system_tmpdir" '}
    [TES] Task submitted: task-b72e6635
    [TES] Task completed: task-b72e6635
    [Tue Nov  8 14:23:02 2022]
    Finished job 1.
    1 of 2 steps (50%) done
    Select jobs to execute...

    [Tue Nov  8 14:23:02 2022]
    localrule all:
        input: ahm2022/bio-hack-test/outfile.txt
        jobid: 0
        resources: tmpdir=/tmp

    [Tue Nov  8 14:23:03 2022]
    Finished job 0.
    2 of 2 steps (100%) done
    Complete log: /home/userName/workspace/biohack2022/.snakemake/log/2022-11-08T142238.560354.snakemake.log
    """)
    stats = textwrap.dedent("""
    {
        "total_runtime": 0.9119722843170166,
        "rules": {
            "processing": {
                "mean-runtime": 0.5975821018218994,
                "min-runtime": 0.5975821018218994,
                "max-runtime": 0.5975821018218994
            },
            "all": {
                "mean-runtime": 0.22511816024780273,
                "min-runtime": 0.22511816024780273,
                "max-runtime": 0.22511816024780273
            }
        },
        "files": {
            "ahm2022/bio-hack-test/outfile.txt": {
                "start-time": "Thu Nov 10 17:10:37 2022",
                "stop-time": "Thu Nov 10 17:10:37 2022",
                "duration": 0.5975821018218994,
                "priority": 0,
                "resources": {
                    "_cores": 1,
                    "_nodes": 1,
                    "tmpdir": "/tmp"
                }
            }
        }
    }
    """)
    with NamedTemporaryFile() as stdout_fh:
        print(stdout, file=stdout_fh)
        with NamedTemporaryFile() as stats_fh:
            print(stats, file=stats_fh)
            start_time = now()
            end_time = start_time + timedelta(hours=1)
            command = ShellCommand(command=[], workdir=Path(os.path.dirname(stats_fh.name)))
            command_result = CommandResult(
                executor=LocalExecutor(),
                stdout_file=Path(stdout_fh.name),
                stderr_file=None,
                stdin_file=None,
                execution_status=ExecutionStatus(code=0),
                process_id=ProcessId(0),
                command=command,
                start_time=start_time,
                end_time=end_time
            )
            result = Snakemake.run_metadata(result=command_result)
            log_dir = Path(".weskit", format_timestamp(start_time))
            assert result == RunMetadata(start_time=start_time,
                                         cmd=command,
                                         workdir=Url(scheme="file",
                                                     path=str(command.workdir)),
                                         log_url=Url(path=str(log_dir)),
                                         stdout_url=Url(path=str(log_dir / "stdout.log")),
                                         stderr_url=Url(path=str(log_dir / "stdout.log")),
                                         output_file_urls=[
                                             Url("ahm2022/bio-hack-test/outfile.txt")
                                         ],
                                         end_time=command_result.end_time,
                                         exit_code=ExecutionStatus(code=0),
                                         job_metadata=job_metadata){
                ("compute_type", "TES"),
                ("compute_url", "https://tesk-na.cloud.e-infra.cz"),
                ("job_id", "task-b72e6635"),
                ("output_file", )
            }
