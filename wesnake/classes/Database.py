import uuid
from wesnake.classes.Run import Run
from wesnake.utils import get_current_time


class Database:
    """ This is a database."""

    def __init__(self, mongo_client, database_name):
        self.db = mongo_client[database_name]
        self.client = mongo_client

    def _db_runs(self):
        return self.db["run"]

    def aggregate_runs(self, pipeline ):
        return dict(self._db_runs().aggregate(pipeline ))

    def get_run(self, run_id: str, **kwargs) -> Run:
        run_data = self._db_runs().find_one(
            filter={"run_id": run_id}, **kwargs)
        if run_data is not None:
            return Run(run_data)
        return None

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
        while not self.get_run(run_id) is None:
            run_id = str(uuid.uuid4())
        return run_id

    def create_new_run(self, request):
        run = Run({
            "run_id": self._create_run_id(),
            "run_status": "UNKNOWN",
            "request_time": self.get_current_time(),
            "request": request
        })
        self._db_runs().insert_one(run.get_data())
        return run

    def update_run(self, run: Run) -> bool:
        if run is None:
            raise ValueError("Run is None")
        return self._db_runs() \
            .update_one({"run_id": run.run_id},
                        {"$set": run.get_data()}
                        ).acknowledged

    def delete_run(self, run: Run) -> bool:
        if run is None:
            raise ValueError("Run is None")
        return self._db_runs() \
            .delete_one({"run_id": run.run_id}) \
            .acknowledged
