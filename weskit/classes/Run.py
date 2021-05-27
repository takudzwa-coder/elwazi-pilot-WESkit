#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from typing import Optional, Dict, List

from weskit.classes.RunStatus import RunStatus


class Run:
    """ This is a Run."""

    def __eq__(self, other):
        return dict(self) == dict(other)

    def __init__(self, data: dict) -> None:

        # Mandatory fields.
        self.__run_id = data["run_id"]
        self.__request_time = data["request_time"]
        self.__request = data["request"]
        self.__user_id = data["user_id"]

        # Optional fields.
        self.celery_task_id = data.get("celery_task_id", None)
        self.execution_path = data.get("execution_path", None)
        self.workflow_path = data.get("workflow_path", None)
        self.outputs = data.get("outputs", {})
        self.execution_log = data.get("execution_log", {})
        self.run_status = RunStatus.\
            from_string(data.get("run_status", "INITIALIZING"))
        self.start_time = data.get("start_time", None)
        self.task_logs = data.get("task_logs", [])
        self.stdout = data.get("stdout", None)
        self.stderr = data.get("stderr", None)

    def __iter__(self):
        """
        This allows casting dict(run).
        """
        for (k, v) in {
            "run_id": self.__run_id,
            "request_time": self.__request_time,
            "request": self.__request,
            "user_id": self.__user_id,
            "celery_task_id": self.celery_task_id,
            "execution_path": self.execution_path,
            "workflow_path": self.workflow_path,
            "outputs": self.outputs,
            "execution_log": self.execution_log,
            "run_status": self.run_status.name,
            "start_time": self.start_time,
            "task_logs": self.task_logs,
            "stdout": self.stdout,
            "stderr": self.stderr
        }.items():
            yield k, v

    @property
    def celery_task_id(self):
        return self.__celery_task_id

    @celery_task_id.setter
    def celery_task_id(self, celery_task_id):
        self.__celery_task_id = celery_task_id

    @property
    def workflow_path(self) -> Optional[str]:
        return self.__workflow_path

    @workflow_path.setter
    def workflow_path(self, workflow_path: Optional[str]):
        self.__workflow_path = workflow_path

    @property
    def execution_path(self):
        return self.__execution_path

    @execution_path.setter
    def execution_path(self, execution_path):
        self.__execution_path = execution_path

    @property
    def request(self):
        return self.__request

    @property
    def run_id(self):
        return self.__run_id

    @property
    def execution_log(self) -> Dict[str, str]:
        return self.__execution_log

    @execution_log.setter
    def execution_log(self, execution_log: Dict[str, str]):
        self.__execution_log = execution_log

    @property
    def run_status(self) -> RunStatus:
        return self.__run_status

    @run_status.setter
    def run_status(self, run_status: RunStatus):
        self.__run_status = run_status

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
    def stdout(self) -> Optional[str]:
        return self.__stdout

    @stdout.setter
    def stdout(self, lines: List[str]):
        self.__stdout = lines

    @property
    def stderr(self) -> Optional[str]:
        return self.__stderr

    @stderr.setter
    def stderr(self, lines: List[str]):
        self.__stderr = lines
