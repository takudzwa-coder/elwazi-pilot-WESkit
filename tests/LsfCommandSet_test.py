# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from datetime import timedelta
from pathlib import Path

from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.classes.executor.cluster.lsf.LsfCommandSet import LsfCommandSet
from weskit.memory_units import Memory


def test_lsf_submit_minimal_command():
    command = LsfCommandSet(). \
        submit(command=ShellCommand(["echo", "Hello, World"]),
               settings=ExecutionSettings())
    assert command.command == [
        'bsub',
        '-env', 'LSB_EXIT_IF_CWD_NOTEXIST=Y',
        '-oo', '/dev/null',
        '-R', "span[hosts=1]",
        "echo 'Hello, World'"]


def test_lsf_submit_full_command():
    command = LsfCommandSet().\
        submit(command=ShellCommand(["bash", "-c", "echo \"hello. $someVar, $someOtherVar\""],
                                    workdir=Path("/some/dir"),
                                    environment={
                                        "some": "someVal",
                                        "someOther": "with, comma",
                                        "space": "here -> "
                                    }),
               stdout_file=Path("/path/to/stdout"),
               stderr_file=Path("/another/pa   th/to/stderr"),
               settings=ExecutionSettings(job_name="da job",
                                          accounting_name="my account",
                                          group="a group",
                                          walltime=timedelta(days=5,
                                                             hours=1,
                                                             minutes=34,
                                                             seconds=45),
                                          memory=Memory.from_str("5G"),
                                          queue="test-queue",
                                          cores=10))
    assert command.command == [
        'bsub',
        '-env',
        "LSB_EXIT_IF_CWD_NOTEXIST=Y, some='someVal', someOther='with, comma', space='here -> '",
        '-cwd', '/some/dir',
        '-oo', '/path/to/stdout',
        '-eo', "/another/pa   th/to/stderr",
        '-J', "da job",
        '-P', "my account",
        '-M', '5242880K',
        '-R', "rusage[mem=5242880K]",
        '-W', '121:34',
        '-G', "a group",
        '-q', 'test-queue',
        '-n', '10',
        '-R', "span[hosts=1]",
        "bash -c 'echo \"hello. $someVar, $someOtherVar\"'"]


def test_get_status():
    command = LsfCommandSet().get_status(["1234", "4567"])
    assert command.command == \
           ["bjobs", "-o", "jobid stat exit_code", "1234", "4567", ss("|"), "tail", "-n", "+2"]


def test_kill():
    ids = ["1234", "3456"]
    command = LsfCommandSet().kill(ids)
    assert command.command == ["bkill", "-s", "TERM"] + ids


def test_wait():
    command = LsfCommandSet().wait_for("1234")
    assert command.command == ["bwait", "-t", "525600", "-w", "ended(1234)"]
