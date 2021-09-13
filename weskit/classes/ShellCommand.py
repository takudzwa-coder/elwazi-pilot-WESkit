#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from builtins import property, str

from typing import Dict, List

from os import PathLike


class ShellCommand:

    def __init__(self,
                 command: List[str],
                 workdir: PathLike,
                 environment: Dict[str, str] = None):
        self.command = command
        if environment is None:
            self.environment = {}
        else:
            self.environment = environment
        self.workdir = workdir

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
    def workdir(self) -> PathLike:
        return self.__workdir

    @workdir.setter
    def workdir(self, workdir: str):
        self.__workdir = workdir

    def __repr__(self) -> str:
        return str(self.__dict__)
