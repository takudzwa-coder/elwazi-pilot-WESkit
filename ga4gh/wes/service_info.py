import os, yaml
from bson.son import SON
from pymongo import MongoClient
from ga4gh.wes.Database import Database
from ga4gh.wes.RunStatus import RunStatus



def connection_to_database():
    connection_url = os.environ["WESNAKE_TEST"]
    database = Database(MongoClient(connection_url), "WES")
    return database


def load_yaml():
    path = os.path.abspath(os.path.join("get_service_info.yaml"))
    with open(path, "r") as ff:
        file = yaml.load(ff, Loader=yaml.FullLoader)
    return file


def rewrite_yaml(file, rewrite_data):
    path = os.path.abspath(os.path.join("get_service_info.yaml"))
    with open(path, "w"):
        new_file = yaml.dump(file, rewrite_data)
    return new_file


def count_states():
    database = connection_to_database()
    count = [
        {"$unwind": "$run_status"},
        {"$group": {"_id": "$run_status", "count": {"$sum": 1}}},
        {"$sort": SON([("_id", 1), ("count", -1)])}
    ]
    return database["run"].aggregate(count)


def rewrite():
    i = 0
    result = count_states()
    result_list = list(result)
    length = len(list(result_list))
    while i < length:
        element = result_list[i]
        # ToDo: replace hard-coded run_status with RunStatus.encode() or RunStatus.decode()
        if element["_id"] == RunStatus.Unknown.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Unknown"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Running.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Running"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Complete.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Complete"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Canceled.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Canceled"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Canceling.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Canceling"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Executor_Error.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Executor_Error"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.System_Error.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["System_Error"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Queued.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Queued"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Initializing.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Initializing"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        elif element["_id"] == RunStatus.Paused.encode():
            data = load_yaml()
            position = data["serviceInfo"]["system_state_counts"]["Paused"]
            result["count"] = position
            rewrite_yaml(load_yaml(), position)
        i = i + 1
