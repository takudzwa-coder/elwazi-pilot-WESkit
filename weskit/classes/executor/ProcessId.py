#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from typing import TypeVar, Generic

import ulid


T = TypeVar("T")


class Identifier(Generic[T]):

    def __init__(self,
                 value: T):
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def __repr__(self) -> str:
        """
        Just a default representation.
        """
        return f"{self.__class__}(value={str(self.value)})"


class WESkitExecutionId(Identifier[ulid.ULID]):
    """
    A process ID assigned by WESkit **before** the submission of a process to the executor.
    This ID can be used to implement failure recovery:

    1. Create WESkitProcessId wid
    2. Store wid in DB
    3a. If no process with wid is in the execution infrastructure, submit a process with wid as ID.
    3b. There is a process with this wid, so get its submission metadata.
    4. Update DB with submission metadata
    """

    def __init__(self):
        """
        ULID based IDs. ULIDs are similar to UUIDs but are sortable by timepoint, which simplifies
        diagnosis and debugging.
        """
        super().__init__(ulid.new())


class ProcessId(Identifier[str]):
    """
    The process ID's value is the native ID of the executor, such as a UNIX PID or a cluster job
    ID assigned by the cluster upon submission. It is available only **after** the submission.

    A process always is executed on some execution infrastructure. This can be a host, a compute
    cluster, etc. Therefore, the process ID additionally has a `where` field.
    """

    def __init__(self,
                 value: str,
                 where: str):
        super().__init__(value)
        self._where = where

    @property
    def where(self) -> str:
        return self._where

    def __repr__(self) -> str:
        """
        Return infrastructure name and process ID as string separated by ::
        """
        return f"{self.where}::{self.value}"
