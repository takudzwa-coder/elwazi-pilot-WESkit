from wesnake.classes.RunStatus import RunStatus

class Run:
    """ This is a Run."""

    def __init__(self, data: dict) -> None:
        # add validation here; those values are required
        self.__run_id = data["run_id"]
        self.__run_status = data["run_status"]
        self.__request_time = data["request_time"]
        self.__request = data["request"]
        
        if "execution_path" in data.keys():
            self.__execution_path = data["execution_path"]
        else:
            self.__execution_path = []
        
        if "run_log" in data.keys():
            self.__run_log = data["run_log"]
        else:
            self.__run_log = {}
        
        if "task_logs" in data.keys():
            self.__task_logs = data["task_logs"]
        else:
            self.__task_logs = []
        
        if "outputs" in data.keys():
            self.__outputs = data["outputs"]
        else:
            self.__outputs = {}
        
        if "celery_task_id" in data.keys():
            self.__celery_task_id = data["celery_task_id"]
        else:
            self.__celery_task_id = None

        if "start_time" in data.keys():
            self.__start_time = data["start_time"]
        else:
            self.__start_time = None

    def get_data(self) -> dict:
        return {
            "celery_task_id": self.__celery_task_id,
            "execution_path": self.__execution_path,
            "request": self.__request,
            "request_time": self.__request_time,
            "run_id": self.__run_id,
            "run_status": self.__run_status,
            "run_log": self.__run_log,
            "outputs": self.__outputs,
            "start_time": self.__start_time,
            "task_logs": self.__task_logs
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

    def run_status_check(self, status:str) -> bool:
        return RunStatus[self.run_status]  == RunStatus[status]

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
        