from weskit.classes.RunStatus import RunStatus


class Run:
    """ This is a Run."""

    def __eq__(self, other):
        return self.get_data() == other.get_data()

    def __init__(self, data: dict) -> None:

        self.__run_id = data["run_id"]
        self.__request_time = data["request_time"]
        self.__request = data["request"]

        self.celery_task_id = data.get("celery_task_id", None)
        self.execution_path = data.get("execution_path", [])
        self.outputs = data.get("outputs", {})
        self.run_log = data.get("run_log", {})
        self.run_status = RunStatus.\
            from_string(data.get("run_status", "UNKNOWN"))
        self.start_time = data.get("start_time", None)
        self.task_logs = data.get("task_logs", [])

    def get_data(self) -> dict:
        return {
            "celery_task_id": self.celery_task_id,
            "execution_path": self.execution_path,
            "request": self.__request,
            "request_time": self.__request_time,
            "run_id": self.__run_id,
            "run_log": self.run_log,
            "run_status": self.run_status.name,
            "outputs": self.outputs,
            "start_time": self.start_time,
            "task_logs": self.task_logs
        }

    def get_run_log(self) -> dict:
        return {
            "run_id": self.__run_id,
            "request": self.__request,
            "state": self.run_status.name,
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
        return self.__outputs

    @start_time.setter
    def start_time(self, start_time: str):
        self.__start_time = start_time
