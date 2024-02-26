# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import uuid
from typing import List, Optional, Callable, Dict

from abc import ABC, abstractmethod

from weskit.classes.Run import Run

logger = logging.getLogger(__name__)


class AbstractDatabase(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def get_run(self, run_id: uuid.UUID, **kwargs) -> Optional[Run]:
        pass

    @abstractmethod
    def get_runs(self, query) -> List[Run]:
        pass

    @abstractmethod
    def list_run_ids_and_stages_and_times(self, user_id: str) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def create_run_id(self) -> uuid.UUID:
        pass

    @abstractmethod
    def insert_run(self, run: Run) -> None:
        pass

    @abstractmethod
    def update_run(self,
                   run: Run,
                   resolution_fun: Optional[Callable[[Run, Run], Run]] = None,
                   max_tries: int = 1) \
            -> Run:
        pass

    @abstractmethod
    def delete_run(self, run: Run) -> bool:
        pass
