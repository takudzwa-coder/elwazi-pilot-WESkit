# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.serializer import to_json


def test_needs_shell():
    cmd1 = ShellCommand(["cat", "a", ">", "b"])
    assert not cmd1.needs_shell()

    cmd2 = ShellCommand(["cat", "a", ss(">"), "b"])
    assert cmd2.needs_shell()


def test_command_expression():
    cmd1 = ShellCommand(["cat", "a", ">", "b"])
    assert cmd1.command_expression == "cat a '>' b"

    cmd2 = ShellCommand(["cat", "a", ss(">"), "b"])
    assert cmd2.command_expression == "cat a > b"


def test_print_shell_special():
    ss1 = ss(">")
    assert str(ss1) == ">"
    assert repr(ss1) == "ss(>)"


def test_eq_and_hash():
    ss0 = ss("x")
    ss1 = ss("a")
    ss2 = ss("a")
    assert ss0 != ss1
    assert ss0.__hash__() != ss1.__hash__()
    assert ss1 == ss2
    assert ss1.__hash__() == ss2.__hash__()


def test_shell_special_serialization():
    data = ["cat", "a", ss(">"), "b"]
    assert to_json(data) == \
           '["cat", "a",' +\
           ' {"__type__": "weskit.classes.ShellCommand.ShellSpecial", "__data__": ">"},' +\
           ' "b"]'


def test_shell_command_serialization():
    data = ShellCommand(command=["cat", "a", ss(">"), "b"],
                        workdir=Path("/some/path"),
                        environment={
                            "var": "value"
                        })
    json = to_json(data)
    assert json == \
        '{"__type__": "weskit.classes.ShellCommand.ShellCommand", "__data__": ' +\
        '{"command": ["cat", "a", {"__type__": "weskit.classes.ShellCommand.ShellSpecial", ' +\
        '"__data__": ">"}, "b"],' + \
        ' "environment": {"var": "value"},' +\
        ' "workdir": {"__type__": "pathlib.PosixPath", "__data__": "/some/path"}}}'
