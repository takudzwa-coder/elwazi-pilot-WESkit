#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from typing import Dict, List


class ShellCommand:

    def __init__(self,
                 command: List[str],
                 workdir: str,
                 environment: Dict[str, str] = {}):
        self.command = command
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
    def workdir(self) -> str:
        return self.__workdir

    @workdir.setter
    def workdir(self, workdir: str):
        self.__workdir = workdir

    def __repr__(self) -> str:
        return str(self.__dict__)
