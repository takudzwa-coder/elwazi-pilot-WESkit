#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, Mapping

from weskit.classes.RunStatus import RunStatus

logger = logging.getLogger(__name__)


class Run:

    def __init__(self, data: Mapping[str, Any]) -> None:
        # WARNING: If you add fields don't forget to add them to __iter__ and merge() and explain
        #          in the code why, in case the field was not added there.

        # Mandatory fields.
        self.__run_id = data["run_id"]
        self.__db_version = data.get("db_version", 0)
        self.__request_time = data["request_time"]
        self.__request = data["request"]
        self.__user_id = data["user_id"]

        # Optional fields.
        self.celery_task_id = data.get("celery_task_id", None)
        self.dir = data.get("run_dir", None)
        self.workflow_path = data.get("workflow_path", None)
        self.outputs = data.get("outputs", {})
        self.log = data.get("execution_log", {})
        self.__status: RunStatus = RunStatus.\
            from_string(data.get("run_status", "INITIALIZING"))
        self.start_time = data.get("start_time", None)
        self.task_logs = data.get("task_logs", [])
        self.stdout = data.get("stdout", None)
        self.stderr = data.get("stderr", None)

        # We keep a copy of the original data in the form of a dictionary representation.
        # Thus, we can detect any modification and don't have to clutter client code with copies
        # of the old run, just to avoid identical replacements in the database.
        self._reference = dict(self)

    @staticmethod
    def _merge_field(field_name: str, we: dict, them: dict, default_value):
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
        a_maybe_before_b = status_b.allowed_to_progress_to(status_a)
        b_maybe_before_a = status_a.allowed_to_progress_to(status_b)
        if a_maybe_before_b and b_maybe_before_a:
            # Reversible state transition. Take the one with higher precedence to disambiguate.
            if status_a.precedence > status_b.precedence:
                return status_a
            else:
                return status_b
        elif a_maybe_before_b:
            return status_a
        else:
            return status_b

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
            copy = Run(self_d)
            # We keep a copy of the original data in the form of a dictionary representation.
            # Thus, we can detect any modification and don't have to clutter client code with copies
            # of the old run, just to avoid identical replacements in the database.
            copy._reference = dict(self)

            # The easy fields:
            copy.celery_task_id = Run._merge_field("celery_task_id", self_d, other_d, None)
            copy.dir = Run._merge_field("run_dir", self_d, other_d, None)
            copy.workflow_path = Run._merge_field("workflow_path", self_d, other_d, None)
            copy.start_time = Run._merge_field("start_time", self_d, other_d, None)
            copy.stdout = Run._merge_field("stdout", self_d, other_d, None)
            copy.stderr = Run._merge_field("stderr", self_d, other_d, None)
            copy.log = Run._merge_field("execution_log", self_d, other_d, {})
            copy.task_logs = Run._merge_field("task_logs", self_d, other_d, [])

            # Fields with special rules
            copy.outputs = Run._merge_outputs(copy.outputs, other.outputs)
            copy.status = Run._merge_status(copy.status, other.status)

            return copy

    def __eq__(self, other):
        return dict(self) == dict(other)

    def __iter__(self):
        """
        This allows casting dict(run).
        """
        for (k, v) in {
            "run_id": self.__run_id,
            "db_version": self.__db_version,
            "request_time": self.__request_time,
            "request": self.__request,
            "user_id": self.__user_id,
            "celery_task_id": self.celery_task_id,
            "run_dir": self.dir,
            "workflow_path": self.workflow_path,
            "outputs": self.outputs,
            "execution_log": self.log,
            "run_status": self.status.name,
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
    def workflow_path(self) -> Optional[str]:
        return self.__workflow_path

    @workflow_path.setter
    def workflow_path(self, workflow_path: Optional[str]):
        self.__workflow_path = workflow_path

    @property
    def dir(self) -> Optional[str]:
        return self.__run_dir

    @dir.setter
    def dir(self, run_dir: Optional[str]):
        self.__run_dir = run_dir

    @property
    def request(self):
        return self.__request

    @property
    def request_time(self):
        return self.__request_time

    @property
    def id(self):
        return self.__run_id

    @property
    def db_version(self):
        """
        The db_version value of the original, unmodified run. The value must only be updated on
        successful update in the database.
        """
        return self.__db_version

    @property
    def log(self) -> Dict[str, Any]:
        return self.__execution_log

    @log.setter
    def log(self, execution_log: Dict[str, Any]):
        self.__execution_log = execution_log

    @property
    def exit_code(self) -> Optional[Any]:
        return self.log.get("exit_code", None)

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
        if self.__status != run_status.name:
            logger.info("Updating state of %s: %s -> %s" %
                        (self.id, self.__status.name, run_status.name))
            self.__status = self.__status.progress_to(run_status)

    @property
    def outputs(self):
        return self.__outputs

    @outputs.setter
    def outputs(self, outputs: dict):
        self.__outputs = outputs

    @property
    def start_time(self):
        return self.__start_time

    @start_time.setter
    def start_time(self, start_time: str):
        self.__start_time = start_time

    @property
    def user_id(self):
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
