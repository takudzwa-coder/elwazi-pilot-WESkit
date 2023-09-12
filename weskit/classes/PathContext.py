# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from weskit.utils import format_timestamp


class PathContext:

    def __init__(self,
                 data_dir: Path,
                 workflows_dir: Path,
                 log_base_subdir: Path = Path(".weskit")):
        self.__data_dir = data_dir
        self.__workflows_dir = workflows_dir
        self.__log_base_subdir = log_base_subdir

    def __eq__(self, other) -> bool:
        return isinstance(other, PathContext) and \
            self.__data_dir == other.__data_dir and \
            self.__workflows_dir == other.__workflows_dir and \
            self.__log_base_subdir == other.__log_base_subdir

    @property
    def data_dir(self) -> Path:
        return self.__data_dir

    @property
    def workflows_dir(self) -> Path:
        return self.__workflows_dir

    @property
    def log_base_subdir(self) -> Path:
        return self.__log_base_subdir

    def encode_json(self):
        return {
            "data_dir": str(self.data_dir),
            "workflows_dir": str(self.workflows_dir)
        }

    @staticmethod
    def decode_json(json: dict):
        return PathContext(data_dir=Path(json["data_dir"]),
                           workflows_dir=Path(json["workflows_dir"]))

    # Methods for context-dependent paths. Note that these have convenience counterparts in Run.
    # Note that these here do not depend on Run, but just the simpler arguments, because they are
    # used in the worker, where there is no Run object.

    def run_dir(self, sub_dir: Path) -> Path:
        return self.data_dir / sub_dir

    def workflow_path(self, sub_dir: Path, rundir_rel_workflow_path: Path) -> Path:
        return self.run_dir(sub_dir) / rundir_rel_workflow_path

    def workdir(self, sub_dir: Path) -> Path:
        return self.run_dir(sub_dir)

    def log_dir(self, sub_dir: Path, time: datetime) -> Path:
        return self.run_dir(sub_dir) / self.log_base_subdir / format_timestamp(time)

    def stderr_file(self, sub_dir: Path, time: datetime) -> Path:
        return self.log_dir(sub_dir, time) / "stderr"

    def stdout_file(self, sub_dir: Path, time: datetime) -> Path:
        return self.log_dir(sub_dir, time) / "stdout"

    def execution_log_file(self, sub_dir: Path, time: datetime) -> Path:
        return self.log_dir(sub_dir, time) / "log.json"
