#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import uuid
from typing import List, Optional, Callable, cast

from bson.son import SON
from pymongo import ReturnDocument, TEXT, MongoClient
from pymongo.results import InsertOneResult
from pymongo.collection import Collection as MongoCollection
from pymongo.database import Database as MongoDatabase

from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.exceptions import ConcurrentModificationError, DatabaseOperationError

logger = logging.getLogger(__name__)


class Database:
    """Database abstraction."""

    def __init__(self, database_url: str, database_name: str):
        """
        Note that the constructor does not try to access the database via the client. It should
        note because otherwise the current thread -- which may be before a fork, e.g. in uWSGI --
        will get its own connection, which will be invalid (or problematic) in the child processes.

        Please initialize the database after the creation of the Flask application by calling
        db.setup(). It will ensure the database exists and is set up (indices, etc.).
        """
        self.database_url = database_url
        self.database_name = database_name

        self.setup_db()
        self.__client: Optional[MongoClient] = None

    def setup_db(self):
        """
        Create the database, collections, and indices.
        """
        client = MongoClient(self.database_url)
        db = client[self.database_name]
        runs = db["run"]
        # Create an index to enforce a uniqueness constraint.
        runs.create_index([("run_id", TEXT)], unique=True)

    def initialize(self):
        if self.__client is None:
            self.__client = MongoClient(self.database_url)

    @property
    def client(self) -> MongoClient:
        self.initialize()
        return cast(MongoClient, self.__client)

    @property
    def _db(self) -> MongoDatabase:
        return self.client[self.database_name]

    @property
    def _runs(self) -> MongoCollection:
        return self._db["run"]

    def aggregate_runs(self, pipeline):
        return dict(self._runs.aggregate(pipeline))

    def get_run(self, run_id: str, **kwargs) -> Optional[Run]:
        run_data = self._runs.find_one(
            filter={"run_id": run_id}, **kwargs)
        if run_data is not None:
            return Run(run_data)
        return None

    def get_runs(self, query) -> List[Run]:
        runs = []
        runs_data = self._runs.find(query)
        if runs_data is not None:
            for run_data in runs_data:
                runs.append(Run(run_data))
        return runs

    def list_run_ids_and_states(self, user_id: str) -> list:
        if user_id is None:
            raise ValueError("Can only list runs for specific user.")
        return list(self._runs.find(
            projection={"_id": False,
                        "run_id": True,
                        "run_status": True,
                        "user_id": True
                        },
            filter={"user_id": user_id}))

    def count_states(self):
        """
        Returns the statistics of all job-states ever, for all users.
        """
        pipeline = [
            {"$unwind": "$run_status"},
            {"$group": {"_id": "$run_status", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        counts_data = list(self._runs.aggregate(pipeline))
        counts = {}
        for counts_datum in counts_data:
            counts[counts_datum["_id"]] = counts_datum["count"]
        for status in RunStatus:
            if status.name not in counts.keys():
                counts[status.name] = 0
        return counts

    def create_run_id(self):
        run_id = str(uuid.uuid4())
        while not self.get_run(run_id) is None:
            run_id = str(uuid.uuid4())
        return run_id

    def insert_run(self, run: Run) -> None:
        try:
            insert_result: InsertOneResult = self._runs.insert_one(dict(run))
        except Exception as e:
            # Wrap the pymongo exception into a WESkitError
            raise DatabaseOperationError(f"Exception during insert_run for {run.id}: {str(e)}") \
                from e
        if not insert_result.acknowledged:
            raise DatabaseOperationError(f"Attempt to insert run {run.id} failed")

    def _update_run(self,
                    run: Run,
                    resolution_fun: Optional[Callable[[Run, Run], Run]] = None,
                    max_tries: int = 1) \
            -> Run:
        # Only update in the database, if the run was actually changed. Specifically, we update
        # only if the db_version field is unchanged. This relies on that the find_one_and_replace
        # function is transactional. On every successful update the db_version counter is
        # incremented.
        updated_run_dict = \
            self._runs. \
            find_one_and_replace({"run_id": run.id, "db_version": run.db_version},
                                 dict(dict(run), db_version=run.db_version + 1),
                                 return_document=ReturnDocument.AFTER)
        if updated_run_dict is None:
            # Nothing updated. Let's search the value that should have been replaced.
            stored_run_dict = self._runs.find_one({"run_id": run.id})
            if stored_run_dict is None:
                # The value is absent! An insert should be done before any update.
                logger.warning(f"Attempted to update non-existing run '{run.id}'")
                raise DatabaseOperationError(f"Attempted to update non-existing run '{run.id}'")
            else:
                if max_tries <= 1:
                    # There is a value in the DB with a different version, but the maximum number
                    # of retries is reached. Stop here.
                    logger.warning(f"Concurrent modification! Finally failed to update '{run.id}'")
                    raise ConcurrentModificationError(run.db_version, run, Run(stored_run_dict))
                else:
                    if resolution_fun is None:
                        # max_tries > 1 but no resolution function is a bug. Thus, no
                        # ConcurrentModificationError but ValueError.
                        raise ValueError(f"Database version of Run '{run.id}' was concurrently "
                                         "updated, but no resolution_fun is defined: db_version "
                                         f"expected '{run.db_version}' != observed "
                                         f"'{stored_run_dict['db_version']}'")
                    else:
                        logger.info(f"Trying to resolve concurrent modification of run '{run.id}'")
                        merged_run = resolution_fun(run, Run(stored_run_dict))
                        return self._update_run(merged_run, resolution_fun, max_tries - 1)
        else:
            return Run(updated_run_dict)

    def update_run(self,
                   run: Run,
                   resolution_fun: Optional[Callable[[Run, Run], Run]] = None,
                   max_tries: int = 1) \
            -> Run:
        """
        Update an existing run in the database using optimistic concurrency control.

        The operation searches a run in the database with the same version as the run that is
        provided to the function (possibly locally updated). If the run is actually unmodified, the
        function retrieves the newest version of the run from the database and returns it.

        If no run can be found with the same version number then it is assumed that the database
        was modified since the original was read. Never modify the db_version of the local `run`!

        If you provided a `resolution_fun(local, db)` function, the local run and the concurrently
        modified value from the database are merged into a single run. If that is not possible,
        then resolution_fun should throw an exception. Maximally max_tries attempts are made
        to resolve concurrent modifications runs, after that a ConcurrentModificationError is
        thrown.

        If a run is found with the same version number then it is replaced with the new one. The
        version number written to the database will be incremented. It is assumed, that this
        value in the database does not have only the same db_version value, but is actually the
        same run.

        Return the new run. If the update is successful the db_version of the new run will be
        incremented. You have to ensure that the input "run" will be discarded and not used for
        another update attempt. You should capture the returned Run object and continue with it.

        If an error occurs, raises a DatabaseModificationError (e.g. if there is no value to be
        modified, because the run was never inserted).

        Note: Usually, data in runs is small, so replacement won't pose a big problem. If there
              are big values (e.g. stderr/stdout of runs) then this operation might get slower,
              though.
        """
        if max_tries < 1:
            raise ValueError(f"I should try to update at least once, got max_tries={max_tries}")
        if max_tries > 1 and resolution_fun is None:
            raise ValueError("No resolution_fun. We cannot merge concurrent modifications")
        if run.modified:
            return self._update_run(run, resolution_fun, max_tries)
        else:
            # If the local run was not modified, return the current version from the database.
            stored_run_dict = self._runs.find_one({"run_id": run.id})
            if stored_run_dict is None:
                # The value is absent! An insert should be done before any update.
                raise DatabaseOperationError(f"Attempted to update non-existing run '{run.id}'")
            else:
                return Run(stored_run_dict)

    def delete_run(self, run: Run) -> bool:
        return self._runs \
            .delete_one({"run_id": run.id}) \
            .acknowledged

    def list_run_ids_and_states_and_times(self, user_id=Optional[str]) -> list:
        filter = None
        if user_id is not None:
            filter = {"user_id": user_id}
        return list(self._runs.find(
            projection={"_id": False,
                        "run_id": True,
                        "run_status": True,
                        # "request_time": True,
                        "start_time": True,
                        "user_id": True,
                        "request": True
                        },
            filter=filter))
