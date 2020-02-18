from datetime import datetime
from bson.json_util import *
from ga4gh.wes.RunStatus import RunStatus


class Database:
    """ This is a database."""

    def __init__(self, mongo_client, database_name):
        self.db = mongo_client[database_name]
        self.client = mongo_client

    def get_run(self, run_id, **kwargs):
        return self._db_runs().find_one({}, filter={"run_id": run_id}, **kwargs)

    def delete_run(self, run_id):
        return self._db_runs().delete_one({"run_id": run_id}).acknowledged

    def list_run_id_and_states(self):
        return self._db_runs().find(
            projection={"_id": False,
                        "run_status": True,
                        "run_id": True
                        })

    def get_workflow_url(self, run_id):
        return self.get_run(run_id).workflow_url

    def get_workflow_params(self, run_id):
        return self.get_run(run_id, projection={"_id": False,
                                                "workflow_params": True
                                                }
                            ).workflow_params

    def disconnect(self):
        self.db.quit()

    def drop(self):
        self.db.drop()

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def create_new_run(self, run_id, request):
        if run_id is None:
            raise ValueError("None can not be run_id!")
        run = {
            "run_id": run_id,
            "run_status": RunStatus.NotStarted.encode(),
            "request_time": self.get_current_time(),
            "request": request,
            "run_log": {},
            "task_logs": [],
            "outputs": {}
        }
        self._db_runs().insert_one(run)
        return run

    def update_run(self, run):
        if run.run_id is None:
            raise ValueError("None can not be run_id!")
        return self._db_runs().update_one({"run_id": run.run_id}, run).acknowledged

    def _db_runs(self):
        return self.db["run"]
