#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations
from builtins import property, str
from pathlib import Path
from typing import Dict, List, Optional


class ShellCommand:

    def __init__(self,
                 command: List[str],
                 workdir: Optional[Path] = None,
                 environment: Dict[str, str] = None):
        self.command = command
        if environment is None:
            self.environment = {}
        else:
            self.environment = environment
        self.workdir = workdir

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
    def command(self) -> List[str]:
        return self.__command

    @command.setter
    def command(self, command: List[str]):
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
