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


class MockDatabase(AbstractDatabase):
    def __init__(self):
        self.runs = {}

    def initialize(self) -> None:
        pass

    def get_run(self, run_id: uuid.UUID, **kwargs) -> Optional[Run]:
        return self.runs.get(run_id)

    def get_runs(self, query) -> List[Run]:
        return [run_data for run_data in self.runs.values()
                if query.get("id") == dict(run_data).get("id") or not query]

    def create_run_id(self) -> uuid.UUID:
        run_id = uuid.uuid4()
        while run_id in self.runs:
            run_id = uuid.uuid4()
        return run_id

    def insert_run(self, run: Run):
        self.runs[run.id] = run.to_bson_serializable()

    def update_run(self, run, resolution_fun=None, max_tries=1) -> Run:
        if run.id not in self.runs:
            raise Exception(f"Run with ID {run.id} not found in the mock database.")
        if max_tries > 1 and resolution_fun is not None:
            stored_run = self.runs[run.id]
            merged_run = resolution_fun(run, stored_run)
            self.runs[run.id] = merged_run
            return merged_run
        else:
            self.runs[run.id] = run
            return run

    def delete_run(self, run) -> bool:
        if run.id in self.runs:
            del self.runs[run.id]
            return True
        return False

    def list_run_ids_and_stages_and_times(self, user_id: str):
        return [{
            "run_id": run["id"],
            "run_stage": run["processing_stage"],
            "start_time": run["start_time"],
            "user_id": run["user_id"],
            "request": run["request"]
        } for run in self.runs.values() if run["user_id"] == user_id]
