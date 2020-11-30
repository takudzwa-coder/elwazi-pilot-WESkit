from wesnake.classes.RunStatus import RunStatus
from datetime import datetime
import uuid


def get_current_time():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


class Database:
    """ This is a database."""

    def __init__(self, mongo_client, database_name):
        self.db = mongo_client[database_name]
        self.client = mongo_client

    def _db_runs(self):
        return self.db["run"]

    def aggregate_states(self, runs):
        return dict(self._db_runs().aggregate(runs))

    def get_run(self, run_id, **kwargs):
        return self._db_runs().find_one(filter={"run_id": run_id}, **kwargs)

    def get_workflow_params(self, run_id):
        return self.get_run(run_id,
                            projection={
                                "_id": False,
                                "request"[0]["workflow_params": True]: False
                            }).workflow_params

    def get_workflow_url(self, run_id):
        return self.get_run(run_id).workflow_url

    def get_current_time(self):
        return get_current_time()

    def list_run_ids_and_states(self):
        return list(self._db_runs().find(
            projection={"_id": False,
                        "run_id": True,
                        "run_status": True
                        }))

    def _create_run_id(self):
        run_id = str(uuid.uuid4())
        while self.get_run(run_id) == run_id:
            run_id = str(uuid.uuid4())
        return run_id

    def create_new_run(self, request):
        run = {
            "run_id": self._create_run_id(),
            "run_status": RunStatus.UNKNOWN.encode(),
            "request_time": self.get_current_time(),
            "request": request,
            "execution_path": [],
            "run_log": {},
            "task_logs": [],
            "outputs": {},
            "celery_task_id": None,
        }
        self._db_runs().insert_one(run)
        return run

    def update_run(self, run):
        if run["run_id"] is None:
            raise ValueError("None can not be run_id")
        return self._db_runs().update_one({"run_id": run["run_id"]},
                                          {"$set": run}
                                          ).acknowledged

    def delete_run(self, run_id):
        return self._db_runs().delete_one({"run_id": run_id}).acknowledged
