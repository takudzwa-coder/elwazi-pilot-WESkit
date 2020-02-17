from _datetime import datetime
from ga4gh.wes.RunStatus import RunStatus


class Database:
    """ This is a database."""

    def __init__(self, mongo_client, database_name):
        self.db = mongo_client[database_name]

    def store_run_id(self, run_id):
        if run_id is None:
            raise ValueError("None can not be run_id!")
        collection_name = run_id
        self.db[collection_name].insert_one(
            {"run_id": run_id}
        )

    def store_run_status(self, run_id, run_status=RunStatus.NotStarted):
        collection_name = run_id
        self.db[collection_name].insert_one(
            {"run_status": run_status}
        )

    def store_run_request_time(self, run_id):
        collection_name = run_id
        self.db[collection_name].insert_one(
            {"request_time": self.get_current_time()}
        )

    def store_run_start_time(self, run_id):
        collection_name = run_id
        self.db[collection_name].insert_one(
            {"start_time": self.get_current_time()}
        )

    def store_run_end_time(self, run_id):
        collection_name = run_id
        self.db[collection_name].insert_one(
            {"end_time": self.get_current_time()}
        )

    def information_run(self, run_id):
        collection_name = run_id
        self.db[collection_name].find()

    def delete_run(self, run_id):
        collection_name = run_id
        self.db[collection_name].remove()

    def list_runs(self):
        self.db.list_collections()

    def get_run_id(self, run_id):
        collection_name = run_id
        self.db[collection_name].findOne({}, {"run_id": 1})

    def get_workflow_url(self, run_id):
        collection_name = run_id
        self.db[collection_name].findOne({}, {"workflow_url": 1})

    def get_workflow_params(self, run_id):
        collection_name = run_id
        self.db[collection_name].findOne({}, {"workflow_params": 1})

    def disconnect(self):
        self.db.quit()

    def drop(self):
        self.db.drop()

    def get_current_time(self):
        datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


    def create_new_run(self, run_id, request):
        if run_id is None:
            raise ValueError("None can not be run_id!")
        run = {
            "run_id": run_id,
            "run_status": RunStatus.NotStarted,
            "request_time": self.get_current_time(),
            "request": request,
            "run_log": {},
            "task_logs": [],
            "outputs": {}
        }
        collection_name = run_id
        self.db[collection_name].insert_one(run)
        return run

    def update_run(self, run):
        if run.run_id is None:
            raise ValueError("None can not be run_id!")
        self.db[run.run_id].update_one(run)