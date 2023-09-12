# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import shlex
from builtins import property, str
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union


class ShellSpecial:
    """
    Special strings that represent strings to be interpreted by the string, such as variables
    ore metacharacters and operators.

    Note that originally this was implemented as subclass of `str`, but that didn't work with the
    serialization, because it was serialized as `str`, effectively upcasting to the more general
    `str` type.
    """

    def __init__(self, value: str):
        self.__value = value

    def __eq__(self, other) -> bool:
        return isinstance(other, type(self)) and self.value == other.value

    def __hash__(self):
        return hash(self.__repr__())

    @property
    def value(self) -> str:
        return self.__value

    def encode_json(self):
        """
        We need to preserve the type information during de-/serialization.
        """
        return self.__value

    @staticmethod
    def decode_json(value) -> ShellSpecial:
        return ShellSpecial(value)

    def __str__(self) -> str:
        """
        Readable string representation, e.g. for users.
        """
        return self.__value

    def __repr__(self) -> str:
        """
        Technical string representation, e.g. for logs.
        """
        return f"ss({self.__value})"


def ss(arg0) -> ShellSpecial:
    """
    Shorthand for ShellSpecial("some string"). 'ss' means shell special.
    Use `ss(some_string)` to mark a string as shell special. Shell specials are quoted differently
    by `ShellCommand.command_expression()`
    """
    return ShellSpecial(arg0)


# A `ShellSegment` is basically a string that the shell identifies during parsing as a unit.
# Usually, these are command or function names and arguments.
CommandSegment = Union[str, ShellSpecial]


class ShellCommand:

    def __init__(self,
                 command: List[CommandSegment],
                 workdir: Optional[Path] = None,
                 environment: Optional[Dict[str, str]] = None):
        self.command = command
        if environment is None:
            self.environment = {}
        else:
            self.environment = environment
        self.workdir = workdir

    def copy(self,
             command: Optional[List[CommandSegment]] = None,
             workdir: Optional[Path] = None,
             environment: Optional[Dict[str, str]] = None):
        return ShellCommand(deepcopy(self.command) if command is None else command,
                            self.workdir if workdir is None else workdir,
                            deepcopy(self.environment) if environment is None else environment)

    def encode_json(self):
        return {
            "command": self.command,
            "environment": self.environment,
            "workdir": self.workdir
        }

    @staticmethod
    def decode_json(values: dict) -> ShellCommand:
        return ShellCommand(**values)

    @property
    def command(self) -> List[CommandSegment]:
        return self.__command

    @command.setter
    def command(self, command: List[CommandSegment]):
        self.__command = command

    @property
    def environment(self) -> Dict[str, str]:
        return self.__environment

    @environment.setter
    def environment(self, environment: Dict[str, str]):
        self.__environment = environment

    @property
    def workdir(self) -> Optional[Path]:
        return self.__workdir

    @workdir.setter
    def workdir(self, workdir: Optional[Path]):
        self.__workdir = workdir

    def __repr__(self) -> str:
        return ", ".join([f"ShellCommand(command={str(self.command)}",
                          f"env={self.environment}",
                          f"workdir={self.workdir})"])

    @property
    def command_expression(self) -> str:
        """
        Produce a string representation of the command. ShellKeywords are not quoted, because that
        would prevent the correct evaluation of the expression by the shell. For instance, in

        source /path/to/script && do --something

        The ampersands can be marked as kw("&&") when constructing the command. Then the quoted
        representation will by

        'source' '/path/to/script/' && 'do' '--something'

        Strings that usually should be marked as non-quoted are, for instance, Bash's
        metacharacters and control operators

        metacharacter:      |  & ; ( ) < > space tab newline
        control operator:   || & && ; ;; ;& ;;& ( ) | |& <newline>
        """
        return " ".join([
            shlex.quote(el) if not isinstance(el, ShellSpecial) else el.value
            for el in self.__command
        ])

    def needs_shell(self) -> bool:
        return any([isinstance(el, ShellSpecial) for el in self.__command])
