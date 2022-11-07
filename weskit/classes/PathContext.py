#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from urllib3.util import Url

from weskit.utils import format_timestamp


class PathContext:
    """
    A `PathContext` represents a joined representation of a set of paths that can be accessed
    in a specific context.

    There are the following general contexts:

    1. the WESkit containers (REST and worker are assumed to be identical)
    2. the compute-infrastructure (head-node and compute node are assumed to be
       identical)
    3. final output locations (all result data are assumed to be put at the same place)

    Note: There is no "input" location. We assume that all necessary files are uploaded via the
          REST call or are retrieved by the workflow. Input files also are not supposed to be
          reported as URLs via the API -- in contrast to output files. Output files may also be
          uploaded by the workflow engine directly.

    For the container and compute contexts there are specific base paths, such as the
    data directory (~ WESKIT_DATA), the workflows directory (~ WESKIT_WORKFLOWS).

    The `PathContext` provides a central object to create URLs for these files that can be used
    to access the data.
    """

    def __init__(self,
                 base_url: Url,
                 data_dir: Path,
                 workflows_dir: Path,
                 log_base_subdir: Path = Path(".weskit")):
        self.__base_url = base_url
        self.__data_dir = data_dir
        self.__workflows_dir = workflows_dir
        self.__log_base_subdir = log_base_subdir

    def __eq__(self, other) -> bool:
        return isinstance(other, PathContext) and \
            self.__base_url == other.__base_url and \
            self.__data_dir == other.__data_dir and \
            self.__workflows_dir == other.__workflows_dir and \
            self.__log_base_subdir == other.__log_base_subdir

    def __iter__(self):
        for (k, v) in {
            "base_url": self.base_url,
            "data_dir": self.data_dir,
            "workflows_dir": self.workflows_dir
        }.items():
            yield k, v

    @property
    def base_url(self) -> Url:
        return self.__base_url

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
        return dict(self)

    @staticmethod
    def decode_json(json: dict):
        return PathContext(**json)

    # Methods for context-dependent paths. Note that these have convenience counterparts in Run.
    # Note that these here do not depend on Run directly, but just the simpler arguments, because
    # they are used in the worker, where there is no Run object.

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
