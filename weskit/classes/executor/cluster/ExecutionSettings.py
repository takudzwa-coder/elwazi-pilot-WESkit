#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import datetime

from weskit.classes.executor.Executor import ExecutionSettings
from weskit.memory_units import Memory


class ClusterExecutionSettings(ExecutionSettings):
    """
    All settings that are not already associated with the command to execute (i.e. without the
    command to execute and the environment for the execution).

    Extend this if you need hosts, storage, swap, GPU, or any other resource.
    """

    def __init__(self,
                 name: str,
                 walltime: datetime.timedelta,
                 memory: Memory):
        self._name = name
        self._walltime = walltime
        self._memory = memory

    @property
    def name(self) -> str:
        return self._name

    @property
    def walltime(self) -> datetime.timedelta:
        return self._walltime

    @property
    def memory(self) -> Memory:
        return self._memory
