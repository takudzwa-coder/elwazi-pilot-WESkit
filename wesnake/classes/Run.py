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

    def get_data(self) -> dict:
        return {
            "run_id": self.__run_id,
            "run_status": self.__run_status,
            "request_time": self.__request_time,
            "request": self.__request,
            "execution_path": self.__execution_path,
            "run_log": self.__run_log,
            "task_logs": self.__task_logs,
            "outputs": self.__outputs,
            "celery_task_id": self.__celery_task_id,
        }

    @property
    def run_id(self):
        return self.__run_id

    @property
    def request(self):
        return self.__request

    @property
    def execution_path(self):
        return self.__execution_path
    
    @execution_path.setter
    def execution_path(self, execution_path):
        self.__execution_path = execution_path

    #@run_id.setter
    #def run_status(self, run_id):
    #    self.run_id = run_id

    @property
    def run_status(self):
        return RunStatus[self.__run_status].name
    
    @run_status.setter
    def run_status(self, run_status):
        self.__run_status = RunStatus[run_status].name

    def check_status(self, status:str) -> bool:
        return RunStatus[self.run_status]  == RunStatus[status]
