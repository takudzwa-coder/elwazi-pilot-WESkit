#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from typing import Optional, List, Dict, Any

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
        self.dir = data.get("run_dir", None)
        self.workflow_path = data.get("workflow_path", None)
        self.outputs = data.get("outputs", {})
        self.log = data.get("execution_log", {})
        self.status = RunStatus.\
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
    def dir(self):
        return self.__run_dir

    @dir.setter
    def dir(self, run_dir):
        self.__run_dir = run_dir

    @property
    def request(self):
        return self.__request

    @property
    def id(self):
        return self.__run_id

    @property
    def log(self) -> Dict[str, Any]:
        return self.__execution_log

    @log.setter
    def log(self, execution_log: Dict[str, Any]):
        self.__execution_log = execution_log

    @property
    def exit_code(self) -> Optional[Any]:
        if self.status == RunStatus.COMPLETE:
            return self.log["exit_code"]
        else:
            return None

    @property
    def status(self) -> RunStatus:
        return self.__status

    @status.setter
    def status(self, run_status: RunStatus):
        self.__status = run_status

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
