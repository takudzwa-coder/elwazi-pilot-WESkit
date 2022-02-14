#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import shlex
from datetime import timedelta
from pathlib import PurePath

from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.classes.executor.cluster.slurm.SlurmCommandSet import SlurmCommandSet
from weskit.memory_units import Memory


def test_slurm_submit_minimal_command():
    command = SlurmCommandSet(). \
        submit(command=ShellCommand(["/tmp/tmp9xbcndui"]),
               settings=ExecutionSettings())
    assert command == [
        'sbatch',
        '--export=NONE',
        '-o', '/dev/null',
        '-N', "1",
        '/tmp/tmp9xbcndui']


def test_slurm_submit_full_command():
    command = SlurmCommandSet().\
        submit(command=ShellCommand(["/tmp/tmp9xbcndui"],
                                    workdir=PurePath("/some/dir"),
                                    environment={
                                        "someVar": "someVal",
                                        "someOtherVar": "containing, a, comma"
                                    }),
               stdout_file=PurePath("/path/to/stdout"),
               stderr_file=PurePath("/another/pa   th/to/stderr"),
               settings=ExecutionSettings(job_name="da job",
                                          accounting_name="my account",
                                          walltime=timedelta(days=5,
                                                             hours=1,
                                                             minutes=34,
                                                             seconds=45),
                                          total_memory=Memory.from_str("5G"),
                                          queue="test-queue",
                                          cores=10))
    print(" ".join(list(map(shlex.quote, command))))
    assert command == [
        'sbatch',
        '--export=someVar=someVal,someOtherVar=\'containing, a, comma\'',
        '-D', '/some/dir',
        '-o', '/path/to/stdout',
        '-e', "/another/pa   th/to/stderr",
        '-J', "da job",
        '-a', "my account",
        '--mem', '5242880K',
        '-t', '121:34:45',
        '-p', 'test-queue',
        '-c', '10',
        '-N', "1",
        '/tmp/tmp9xbcndui']


def test_get_status():
    command = SlurmCommandSet().get_status(["1234", "4567"])
    assert command == ["bash", "-c", "sacct --format=JobID,State,ExitCode -j '1234,4567' -n -X"]


def test_kill():
    ids = ["1234", "3456"]
    command = SlurmCommandSet().kill(ids)
    assert command == ["scancel", "-s", "TERM"] + ids
