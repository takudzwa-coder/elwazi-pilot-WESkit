from datetime import datetime
from bson.json_util import *
from ga4gh.wes.RunStatus import RunStatus


class Database:
    """ This is a database."""

    def __init__(self, mongo_client, database_name):
        self.db = mongo_client[database_name]
        self.client = mongo_client

    def _db_runs(self):
        return self.db["run"]
    
    def get_run(self, run_id, **kwargs):
        return self._db_runs().find_one(filter={"run_id": run_id}, **kwargs)
    
    def get_workflow_params(self, run_id):
        return self.get_run(run_id, projection={"_id": False,
                                                "request"[0]["workflow_params": True]: False
                                                }
                            ).workflow_params
    
    def get_workflow_url(self, run_id):
        return self.get_run(run_id).workflow_url

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def list_run_ids_and_states(self):
        return list(self._db_runs().find(
            projection={"_id": False,
                        "run_id": True,
                        "run_status": True
                        }))
    
    def create_new_run(self, run_id, request):
        if run_id is None:
            raise ValueError("None can not be run_id!")
        run = {
            "run_id": run_id,
            "run_status": RunStatus.NotStarted.encode(),
            "request_time": self.get_current_time(),
            "request": [{"workflow_url": request,
                        "workflow_params": request
                         }],
            "environment_path": request,
            "run_log": {},
            "task_logs": [],
            "outputs": {}
        }
        self._db_runs().insert_one(run)
        return run

    def update_run(self, run):
        if run["run_id"] is None:
            raise ValueError("None can not be run_id!")
        return self._db_runs().update_one({"run_id": run["run_id"]}, {"$set": run}).acknowledged

    def delete_run(self, run_id):
        return self._db_runs().delete_one({"run_id": run_id}).acknowledged
