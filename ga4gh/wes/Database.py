from pymongo import MongoClient
from _datetime import datetime


client = MongoClient()
db = client["python_db"]


class Database:
    """ This is a database."""

    def store_run_id(self, run_id):
        collection_name = run_id
        db[collection_name].insert(
            {"run_id": run_id}
        )

    def store_run_status(self, run_id):
        collection_name = run_id
        db[collection_name].insert(
            {"run_status": state}
        )

    def store_run_request_time(self, run_id):
        collection_name = run_id
        db[collection_name].insert(
            {"request_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        )

    def store_run_start_time(self, run_id):
        collection_name = run_id
        db[collection_name].insert(
            {"start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        )

    def store_run_end_time(self, run_id):
        collection_name = run_id
        db[collection_name].insert(
            {"end_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        )

    def information_run(self, run_id):
        collection_name = run_id
        db[collection_name].find().pretty()

    def delete_run(self, run_id):
        collection_name = run_id
        db[collection_name].remove()

    def list_runs(self):
        db.list_collections()

    def get_run_id(self, run_id):
        collection_name = run_id
        db[collection_name].findOne({}, {"run_id": 1})

    def get_workflow_url(self, run_id):
        collection_name = run_id
        db[collection_name].findOne({}, {"workflow_url": 1})

    def get_workflow_params(self, run_id):
        collection_name = run_id
        db[collection_name].findOne({}, {"workflow_params": 1})
