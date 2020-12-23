from wesnake.classes.RunStatus import RunStatus

class Run:
    """ This is a Run."""

    def __init__(self, data: dict) -> None:
        # add validation here; those values are required
        self.run_id = data["run_id"]
        self.run_status = data["run_status"]
        self.request_time = data["request_time"]
        self.request = data["request"]
        
        if "execution_path" in data.keys():
            self.execution_path = data["execution_path"]
        else:
            self.execution_path = []
        
        if "run_log" in data.keys():
            self.run_log = data["run_log"]
        else:
            self.run_log = {}
        
        if "task_logs" in data.keys():
            self.task_logs = data["task_logs"]
        else:
            self.task_logs = []
        
        if "outputs" in data.keys():
            self.outputs = data["outputs"]
        else:
            self.outputs = {}
        
        if "celery_task_id" in data.keys():
            self.celery_task_id = data["celery_task_id"]
        else:
            self.celery_task_id = None

    def get_data(self) -> dict:
        return {
            "run_id": self.run_id,
            "run_status": self.run_status,
            "request_time": self.request_time,
            "request": self.request,
            "execution_path": self.execution_path,
            "run_log": self.run_log,
            "task_logs": self.task_logs,
            "outputs": self.outputs,
            "celery_task_id": self.celery_task_id,
        }
    
    def set_status(self, status: str) -> None:
        self.run_status = RunStatus[status].name
    
    def get_status(self) -> str:
        return RunStatus[self.run_status].name
    
    def check_status(self, status:str) -> bool:
        return RunStatus[self.run_status]  == RunStatus[status]
