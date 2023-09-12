# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
import uuid
from typing import List, Optional, Callable, cast, Dict, Sequence, Mapping, Any

from bson import CodecOptions, UuidRepresentation, InvalidDocument
from bson.son import SON
from pymongo import ReturnDocument, MongoClient
from pymongo.collection import Collection as MongoCollection
from pymongo.database import Database as MongoDatabase
from pymongo.results import InsertOneResult

from weskit.classes.Run import Run
from weskit.exceptions import ConcurrentModificationError, DatabaseOperationError

logger = logging.getLogger(__name__)


class Database:
    """Database abstraction."""

    def __init__(self, server_url: str, database_name: str):
        """
        Note that the constructor does not try to access the database via the client. It should
        note because otherwise the current thread -- which may be before a fork, e.g. in uWSGI --
        will get its own connection, which will be invalid (or problematic) in the child processes.

        Please initialize the database after the creation of the Flask application by calling
        db.setup(). It will ensure the database exists and is set up (indices, etc.).
        """
        self.server_url = server_url
        self.database_name = database_name

        self.__client: Optional[MongoClient] = None
        self.__db: Optional[MongoDatabase] = None

    def initialize(self):
        if self.__client is None:
            # For encoding/decoding with bson see
            # See https://pymongo.readthedocs.io/en/stable/examples/uuid.html#standard
            # and https://pymongo.readthedocs.io/en/stable/examples/custom_type.html#custom-type-example  # noqa
            # Philip: I tried this but then MongoDB converted every string to Path. Could not
            #         figure out how to convert just the path-encoding strings back to Path.
            self.__client = MongoClient(self.server_url)

            self.__db = MongoDatabase(self.__client, self.database_name)

            # Create an index to enforce a uniqueness constraint.
            runs = self.__db["run"]
            runs.create_index("id", unique=True)

    @property
    def client(self) -> MongoClient:
        self.initialize()
        return cast(MongoClient, self.__client)

    @property
    def db(self) -> MongoDatabase:
        self.initialize()
        return cast(MongoDatabase, self.__db)

    @property
    def _runs(self) -> MongoCollection:
        return self.db.get_collection("run",
                                      codec_options=CodecOptions(
                                          uuid_representation=UuidRepresentation.STANDARD))

    def aggregate_runs(self, pipeline):
        return dict(self._runs.aggregate(pipeline))

    def get_run(self, run_id: uuid.UUID, **kwargs) -> Optional[Run]:
        run_data = self._runs.find_one(
            filter={"id": run_id},
            projection={"_id": False},
            **kwargs)
        if run_data is not None:
            return Run.from_bson_serializable(run_data)
        else:
            return None

    def get_runs(self, query) -> List[Run]:
        runs = []
        runs_data = self._runs.find(query,
                                    projection={"_id": False})
        if runs_data is not None:
            for run_data in runs_data:
                runs.append(Run.from_bson_serializable(run_data))
        return runs

    def list_run_ids_and_stages(self, user_id: str) -> List[Dict[str, str]]:
        if user_id is None:
            raise ValueError("Can only list runs for specific user.")
        return list(self._runs.find(
            projection={"_id": False,
                        "id": True,
                        "exit_code": True,
                        "processing_stage": True,
                        "user_id": True,
                        },
            filter={"user_id": user_id}))

    def count_states(self) -> List[Any]:
        """
        Returns the statistics of all job-states ever, for all users.
        """
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$unwind": "$processing_stage"},
            {"$group": {"_id": {"processing_stage": "$processing_stage",
                                "exit_code": "$exit_code"
                                }, "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        counts_data = list(self._runs.aggregate(pipeline))
        return counts_data

    def create_run_id(self) -> uuid.UUID:
        run_id = uuid.uuid4()
        while not self.get_run(run_id) is None:
            run_id = uuid.uuid4()
        return run_id

    def insert_run(self, run: Run) -> None:
        try:
            insert_result: InsertOneResult = self._runs.insert_one(run.to_bson_serializable())
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
        logger.debug(f"Trying to update run {run.id} in database (left tries = {max_tries})")
        try:
            updated_run_dict = \
                self._runs. \
                find_one_and_replace({"id": run.id, "db_version": run.db_version},
                                     dict(run.to_bson_serializable(),
                                          db_version=run.db_version + 1),
                                     return_document=ReturnDocument.AFTER,
                                     projection={'_id': False})
            if updated_run_dict is None:
                # Nothing updated. Let's search the value that should have been replaced.
                stored_run_dict = self._runs.find_one({"id": run.id},
                                                      projection={"_id": False})
                if stored_run_dict is None:
                    # The value is absent! An insert should be done before any update.
                    raise DatabaseOperationError("Attempted to update non-existing run "
                                                 f"'{run.id}'")
                else:
                    if max_tries <= 1:
                        # There is a value in the DB with a different version, but the maximum
                        # number of retries is reached. Stop here.
                        raise ConcurrentModificationError(
                            run.db_version,
                            run,
                            Run.from_bson_serializable(stored_run_dict))
                    else:
                        if resolution_fun is None:
                            # max_tries > 1 but no resolution function is a bug. Thus, no
                            # ConcurrentModificationError but ValueError.
                            raise ValueError(f"Database version of Run '{run.id}' was concurrently "
                                             "updated, but no resolution_fun is defined: "
                                             f"db_version expected '{run.db_version}' != observed "
                                             f"'{stored_run_dict['db_version']}'")
                        else:
                            logger.debug("Trying to resolve concurrent modification of run "
                                         f"'{run.id}'")
                            merged_run = resolution_fun(run,
                                                        Run.from_bson_serializable(stored_run_dict))
                            return self._update_run(merged_run, resolution_fun, max_tries - 1)
            else:
                return Run.from_bson_serializable(updated_run_dict)
        except InvalidDocument as ex:
            raise DatabaseOperationError(f"DB error with run {run.id}: {run}", ex)

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
            stored_run_dict = self._runs.find_one({"id": run.id},
                                                  projection={"_id": False})
            if stored_run_dict is None:
                # The value is absent! An insert should be done before any update.
                raise DatabaseOperationError(f"Attempted to update non-existing run '{run.id}'")
            else:
                return Run.from_bson_serializable(stored_run_dict)

    def delete_run(self, run: Run) -> bool:
        return self._runs \
            .delete_one({"id": run.id}) \
            .acknowledged

    def list_run_ids_and_stages_and_times(self, user_id: str) -> list:
        if user_id is None:
            raise ValueError("Can only list runs for specific user.")
        return list(map(
            lambda r: {
                "run_id": r["id"],
                "run_stage": r["processing_stage"],
                "start_time": r["start_time"],
                "user_id": r["user_id"],
                "request": r["request"]
            },
            self._runs.find(filter={"user_id": user_id})))
