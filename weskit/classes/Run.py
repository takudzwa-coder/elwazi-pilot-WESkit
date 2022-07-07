#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Mapping
from uuid import UUID

from weskit.classes.PathContext import PathContext
from weskit.classes.RunStatus import RunStatus
from weskit.utils import format_timestamp, from_formatted_timestamp, updated
from weskit.utils import mop

logger = logging.getLogger(__name__)


class Run:
    """
    Note that some fields are translated into str and can be provided typed or as str for the
    sake of simplicity when doing serialization.
    """

    def __init__(self,
                 id: UUID,
                 request_time: datetime,
                 request: dict,
                 user_id: str,
                 db_version: int = 0,
                 celery_task_id: Optional[str] = None,
                 sub_dir: Optional[Path] = None,
                 rundir_rel_workflow_path: Optional[Path] = None,
                 outputs: Dict[str, List[str]] = None,
                 execution_log: Optional[Dict[str, Any]] = None,
                 status: RunStatus = RunStatus.INITIALIZING,
                 start_time: Optional[datetime] = None,
                 task_logs: Optional[list] = None,
                 stdout: Optional[List[str]] = None,
                 stderr: Optional[List[str]] = None
                 ) -> None:
        # WARNING: If you add fields don't forget to add them to __iter__ and merge() and explain
        #          in the code why, in case the field was not added there.
        self.__id = id
        self.__db_version = db_version
        self.__request_time = request_time
        self.__request = request
        self.__user_id = user_id
        self.celery_task_id = celery_task_id
        self.sub_dir = sub_dir
        self.rundir_rel_workflow_path = rundir_rel_workflow_path
        self.outputs = {} if outputs is None else outputs
        if execution_log is None:
            self.execution_log = {}
        else:
            self.execution_log = execution_log
        # Direct field access for initial setting of the status. Afterwards controlled progression
        # with accessors.
        self.__status = status
        self.start_time = start_time
        self.task_logs = task_logs
        self.stdout = stdout
        self.stderr = stderr

        # We keep a copy of the original data in the form of a dictionary representation.
        # Thus, we can detect any modification and don't have to clutter client code with copies
        # of the old run, just to avoid identical replacements in the database.
        self._reference = dict(self)

    @staticmethod
    def _merge_field(field_name: str, we: dict, them: dict, default_value):
        """
        Two values can be reconciled, if they are identical or if one of them is the default
        value. If both values differ from the default, raise an exception.
        """
        if we[field_name] == them[field_name]:
            return we[field_name]
        elif we[field_name] is default_value:
            return them[field_name]
        elif them[field_name] is default_value:
            return we[field_name]
        else:
            raise RuntimeError(
                f"Could not merge field '{field_name}':\n\twe={we}\n\tthem={them}")

    @staticmethod
    def _merge_outputs(old_outputs: Dict[str, List[str]],
                       other_outputs: Dict[str, List[str]]) \
            -> Dict[str, List[str]]:
        """
        Outputs may have been modified after the retrieval of the execution result via
        Celery, e.g. to enrich with S3 URIs. The outputs are a dictionary of lists,
        but basically the order is irrelevant. So it could be considered a dictionary of
        sets that are trivially merged.
        """
        # We need to copy the dictionaries, otherwise self will be modified.
        new_outputs: Dict[str, List[str]] = \
            {key: values for key, values in old_outputs.items()}
        for key, values in other_outputs.items():
            if key in new_outputs:
                new_outputs[key] = list(set(new_outputs[key]).union(values))
            else:
                new_outputs[key] = values
        return new_outputs

    @staticmethod
    def _merge_status(status_a: RunStatus, status_b: RunStatus) -> RunStatus:
        """
        If a transition between the two states is allowed, simply choose the more progressed
        state based on its precedence. We cannot make any assumptions about whether self or
        other is more progressed (the nature of concurrency). Therefore, select the more
        progressed state of the two Runs (i.e. ignore parameter order).
        """
        if status_a == status_b:
            return status_a

        b_may_progress_to_a = status_b.allowed_to_progress_to(status_a)
        a_may_progress_to_b = status_a.allowed_to_progress_to(status_b)
        if b_may_progress_to_a and a_may_progress_to_b:
            # Reversible state transition. Take the one with higher precedence to disambiguate.
            if status_a.precedence > status_b.precedence:
                return status_a
            elif status_a.precedence < status_b.precedence:
                return status_b
            else:
                raise RuntimeError("Bug! Different RunStatus with same precedence! "
                                   f"{status_a.name} and {status_b.name}")
        elif b_may_progress_to_a:
            return status_a
        elif a_may_progress_to_b:
            return status_b
        else:
            raise RuntimeError(
                "No progression rules for status "
                f"A = {status_a.name} and B = {status_b.name}")

    def merge(self, other: Run) -> Run:
        """
        Attempt to merge another Run into this Run. Note that self is not modified, but a copy is
        returned. The following rules are used

        * Optional fields are set to the unambiguous value != None.
        * All fields where both Runs have a non-None value are accepted, if the value is the same.
        * If a field has different non-None value in the two Runs
        * The new run will be marked as modified if any of the self-fields have been modified.
        """

        if self.id != other.id or \
                self.request_time != other.request_time or \
                self.request != other.request or \
                self.user_id != other.user_id:
            # db_version is not tested, because the whole point of merge is to resolve concurrent
            # modifications.
            raise RuntimeError(f"Cannot merge runs:\t\nself={self}\n\tother={other}")
        else:
            self_d = dict(self)
            other_d = dict(other)
            copy = Run(**self_d)
            # We keep a copy of the original data in the form of a dictionary representation.
            # Thus, we can detect any modification and don't have to clutter client code with copies
            # of the old run, just to avoid identical replacements in the database.
            copy._reference = dict(self)

            # The easy fields:
            copy.celery_task_id = Run._merge_field("celery_task_id", self_d, other_d, None)
            copy.sub_dir = Run._merge_field("sub_dir", self_d, other_d, None)
            copy.rundir_rel_workflow_path = Run._merge_field("rundir_rel_workflow_path",
                                                             self_d, other_d, None)
            copy.start_time = Run._merge_field("start_time", self_d, other_d, None)
            copy.stdout = Run._merge_field("stdout", self_d, other_d, None)
            copy.stderr = Run._merge_field("stderr", self_d, other_d, None)
            copy.execution_log = Run._merge_field("execution_log", self_d, other_d, {})
            copy.task_logs = Run._merge_field("task_logs", self_d, other_d, [])

            # Fields with special rules
            copy.outputs = Run._merge_outputs(copy.outputs, other.outputs)
            copy.status = Run._merge_status(copy.status, other.status)

            return copy

    def to_bson_serializable(self):
        """
        Create a BSON serializable object to be put into MongoDB.
        """
        result = dict(self)
        result = updated(result,
                         sub_dir=mop(result["sub_dir"], str),
                         rundir_rel_workflow_path=mop(result["rundir_rel_workflow_path"], str),
                         request_time=mop(result["request_time"], format_timestamp),
                         start_time=mop(result["start_time"], format_timestamp),
                         status=result["status"].name)
        return result

    @staticmethod
    def from_bson_serializable(values: Mapping[str, Any]) -> Run:
        """
        Construct Run from what was read from MongoDB.
        """
        args = updated(values,
                       sub_dir=mop(values["sub_dir"], Path),
                       rundir_rel_workflow_path=mop(values["rundir_rel_workflow_path"], Path),
                       request_time=mop(values["request_time"], from_formatted_timestamp),
                       start_time=mop(values["start_time"], from_formatted_timestamp),
                       status=RunStatus.from_string(values["status"]))
        return Run(**args)

    def __eq__(self, other):
        return dict(self) == dict(other)

    def __iter__(self):
        """
        This allows casting dict(run) and the reverse with Run(**run_dict).
        """
        for (k, v) in {
            "id": self.__id,
            "db_version": self.__db_version,
            "request_time": self.__request_time,
            "request": self.__request,
            "user_id": self.__user_id,
            "celery_task_id": self.celery_task_id,
            "sub_dir": self.sub_dir,
            "rundir_rel_workflow_path": self.rundir_rel_workflow_path,
            "outputs": self.outputs,
            "execution_log": self.execution_log,
            "status": self.status,
            "start_time": self.start_time,
            "task_logs": self.task_logs,
            "stdout": self.stdout,
            "stderr": self.stderr
        }.items():
            yield k, v

    def __str__(self):
        return f"Run({dict(self)})"

    @property
    def modified(self) -> bool:
        return dict(self) != self._reference

    @property
    def celery_task_id(self) -> Optional[str]:
        return self.__celery_task_id

    @celery_task_id.setter
    def celery_task_id(self, celery_task_id: Optional[str]):
        self.__celery_task_id = celery_task_id

    @property
    def rundir_rel_workflow_path(self) -> Optional[Path]:
        return self.__rundir_rel_workflow_path

    @rundir_rel_workflow_path.setter
    def rundir_rel_workflow_path(self, workflow_path: Optional[Path]):
        if workflow_path is not None:
            if workflow_path.is_absolute():
                raise ValueError("Run.workflow_path must be relative path")
        self.__rundir_rel_workflow_path = workflow_path

    @property
    def sub_dir(self) -> Optional[Path]:
        return self.__run_dir

    @sub_dir.setter
    def sub_dir(self, rel_run_dir: Optional[Path]):
        if rel_run_dir is not None:
            if rel_run_dir.is_absolute():
                raise ValueError("Run.dir must be relative path")
        self.__run_dir = rel_run_dir

    @property
    def request(self):
        return self.__request

    @property
    def request_time(self) -> datetime:
        return self.__request_time

    @property
    def id(self) -> UUID:
        return self.__id

    @property
    def db_version(self) -> int:
        """
        The db_version value of the original, unmodified run. The value must only be updated on
        successful update in the database.
        """
        return self.__db_version

    @property
    def execution_log(self) -> Dict[str, Any]:
        return self.__execution_log

    @execution_log.setter
    def execution_log(self, execution_log: Dict[str, Any]):
        self.__execution_log = execution_log

    @property
    def exit_code(self) -> Optional[Any]:
        return self.execution_log.get("exit_code", None)

    @property
    def status(self) -> RunStatus:
        return self.__status

    @status.setter
    def status(self, run_status: RunStatus):
        """
        Update the Run.status, but guard against invalid state transitions. This early test
        prevents that invalid state changes get persisted into database and follows the
        "fail early" principle.
        """
        if self.__status != run_status:
            logger.debug("Updating state of %s: %s -> %s" %
                         (self.id, self.__status.name, run_status.name))
            self.__status = self.__status.progress_to(run_status)

    @property
    def outputs(self) -> Dict[str, List[str]]:
        return self.__outputs

    @outputs.setter
    def outputs(self, outputs: Dict[str, List[str]]):
        self.__outputs = outputs

    @property
    def start_time(self) -> Optional[datetime]:
        return self.__start_time

    @start_time.setter
    def start_time(self, start_time: Optional[datetime]):
        self.__start_time = start_time

    @property
    def user_id(self) -> str:
        return self.__user_id

    @property
    def stdout(self) -> Optional[List[str]]:
        return self.__stdout

    @stdout.setter
    def stdout(self, lines: List[str]):
        self.__stdout = lines

    @property
    def stderr(self) -> Optional[List[str]]:
        return self.__stderr

    @stderr.setter
    def stderr(self, lines: List[str]):
        self.__stderr = lines

    # Methods for context-dependent paths. E.g. in docker container, or on remote host.
    # Dependent on whether self.dir is set or not, these methods may return None.
    # All these return paths relative to the base of the `PathContext`. Usually the PathContext
    # will be an absolute path.

    def run_dir(self, context: PathContext) -> Optional[Path]:
        return context.run_dir(self.sub_dir) \
            if self.sub_dir is not None else None

    def workflow_path(self, context: PathContext) -> Optional[Path]:
        return context.workflow_path(self.sub_dir, self.rundir_rel_workflow_path) \
            if self.sub_dir is not None and self.rundir_rel_workflow_path is not None else None

    def workdir(self, context: PathContext) -> Optional[Path]:
        return context.run_dir(self.sub_dir) \
            if self.sub_dir is not None else None

    def log_dir(self, context: PathContext) -> Optional[Path]:
        return context.log_dir(self.sub_dir, self.start_time) \
            if self.sub_dir is not None and self.start_time is not None else None

    def stderr_file(self, context: PathContext) -> Optional[Path]:
        return context.stderr_file(self.sub_dir, self.start_time) \
            if self.sub_dir is not None and self.start_time is not None else None

    def stdout_file(self, context: PathContext) -> Optional[Path]:
        return context.stdout_file(self.sub_dir, self.start_time) \
            if self.sub_dir is not None and self.start_time is not None else None

    def execution_log_file(self, context: PathContext) -> Optional[Path]:
        return context.execution_log_file(self.sub_dir, self.start_time) \
            if self.sub_dir is not None and self.start_time is not None else None
