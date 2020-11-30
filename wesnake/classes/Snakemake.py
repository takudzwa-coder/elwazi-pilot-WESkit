from wesnake.classes.RunStatus import RunStatus
from wesnake.tasks.snakemake import run_snakemake
from celery.task.control import revoke
import json
import os
import yaml


celery_to_wes_state = {
    "PENDING": "QUEUED",
    "STARTED": "RUNNING",
    "SUCCESS": "COMPLETE",
    "FAILURE": "EXECUTOR_ERROR",
    "RETRY": "QUEUED",
    "REVOKED": "CANCELED"}


running_states = [
    "UNKNOWN",
    "QUEUED",
    "INITIALIZING",
    "RUNNING",
    "PAUSED"]


def mycast(value, type):
    if type == "int":
        return int(value)
    if type == "str":
        return str(value)
    if type == "float":
        return float(value)


class Snakemake:
    def __init__(self, config, datadir):
        self.kwargs = {}
        for parameter in (config["static_service_info"]
                                ["default_workflow_engine_parameters"]):
            self.kwargs[parameter["name"]] = mycast(
                value=parameter["default_value"],
                type=parameter["type"])
        self.datadir = datadir

    def cancel(self, run, database):
        revoke(run["_celery_task_id"], terminate=True, signal='SIGKILL')
        run["run_status"] = RunStatus.CANCELED.encode()
        database.update_run(run)
        return run

    def get_state(self, run, database):
        # check if task is running and update state
        if run["run_status"] in running_states:
            running_task = run_snakemake.AsyncResult(run["_celery_task_id"])
            run["run_status"] = celery_to_wes_state[running_task.state]
            database.update_run(run)
        return run["run_status"]

    def execute(self, run, database):

        run_dir = os.path.abspath(os.path.join(self.datadir, run["run_id"]))
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
        run["execution_path"] = run_dir
        database.update_run(run)

        # execute run
        run_kwargs = {
            "snakefile": run["request"]["workflow_url"],
            "workdir": run_dir,
            "configfiles": [os.path.join(run_dir, "config.yaml")]
        }
        run["run_status"] = RunStatus.INITIALIZING.encode()
        run["start_time"] = database.get_current_time()
        run["run_log"]["cmd"] = ", ".join(
            "{}={}".format(key, run_kwargs[key]) for key in run_kwargs.keys()
        )
        database.update_run(run)
        task = run_snakemake.apply_async(
            args=[],
            kwargs={**run_kwargs, **self.kwargs})
        run["_celery_task_id"] = task.id
        database.update_run(run)
        return run
