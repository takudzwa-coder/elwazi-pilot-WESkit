from wesnake.classes.RunStatus import RunStatus


class Run:
    """ This is a Run."""

    def __init__(self, data: dict) -> None:

        try:
            self.__run_id = data["run_id"]
            self.__request_time = data["request_time"]
            self.__request = data["request"]
        except KeyError:
            raise

        if "celery_task_id" in data.keys():
            self.celery_task_id = data["celery_task_id"]
        else:
            self.celery_task_id = None

        if "execution_path" in data.keys():
            self.execution_path = data["execution_path"]
        else:
            self.execution_path = []

        if "outputs" in data.keys():
            self.outputs = data["outputs"]
        else:
            self.outputs = {}

        if "run_log" in data.keys():
            self.run_log = data["run_log"]
        else:
            self.run_log = {}

        if "run_status" in data.keys():
            self.run_status = data["run_status"]
        else:
            self.run_status = "UNKNOWN"

        if "start_time" in data.keys():
            self.start_time = data["start_time"]
        else:
            self.start_time = None

        if "task_logs" in data.keys():
            self.task_logs = data["task_logs"]
        else:
            self.task_logs = []

    def get_data(self) -> dict:
        return {
            "celery_task_id": self.celery_task_id,
            "execution_path": self.execution_path,
            "request": self.__request,
            "request_time": self.__request_time,
            "run_id": self.__run_id,
            "run_log": self.run_log,
            "run_status": self.run_status,
            "outputs": self.outputs,
            "start_time": self.start_time,
            "task_logs": self.task_logs
        }

    def get_run_log(self) -> dict:
        return {
            "run_id": self.__run_id,
            "request": self.__request,
            "state": self.run_status,
            "run_log": self.run_log,
            "task_logs": self.task_logs,
            "outputs": self.outputs
        }


    @property
    def celery_task_id(self):
        return self.__celery_task_id

    @celery_task_id.setter
    def celery_task_id(self, celery_task_id):
        self.__celery_task_id = celery_task_id

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
    def run_log(self):
        return self.__run_log

    @run_log.setter
    def run_log(self, run_log: str):
        self.__run_log = run_log

    @property
    def run_status(self):
        return RunStatus[self.__run_status].name

    @run_status.setter
    def run_status(self, run_status: str):
        self.__run_status = RunStatus[run_status].name

    def run_status_check(self, status: str) -> bool:
        return RunStatus[self.run_status] == RunStatus[status]

    @property
    def outputs(self):
        return self.__outputs

    @outputs.setter
    def outputs(self, outputs: dict):
        self.__outputs = outputs

    @property
    def start_time(self):
        return self.__outputs

    @start_time.setter
    def start_time(self, start_time: str):
        self.__start_time = start_time
