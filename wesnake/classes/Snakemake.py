from wesnake.classes.RunStatus import RunStatus
from wesnake.tasks.snakemake import run_snakemake
from celery.task.control import revoke
from werkzeug.utils import secure_filename
from wesnake.utils import get_current_time
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

EXECUTOR_WF_NOT_FOUND = """
WESnake executor error: the workflow file was not found. Please provide either
a url with a workflow file on the server or attach a workflow
via workflow_attachments."""


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

    def cancel(self, run):
        revoke(run["_celery_task_id"], terminate=True, signal='SIGKILL')
        run["run_status"] = RunStatus.CANCELED.encode()
        return run

    def get_state(self, run):
        # check if task is running and update state
        if run["run_status"] in running_states:
            running_task = run_snakemake.AsyncResult(run["_celery_task_id"])
            run["run_status"] = celery_to_wes_state[running_task.state]
        return run["run_status"]

    # checks if workflow has absolute url (on server) or is attached in files
    def _check_workflow_files(self, run, files):
        if os.path.isabs(run["request"]["workflow_url"]):
            if os.path.isfile(run["request"]["workflow_url"]):
                return True
        elif "workflow_attachment" in files:
            workflow_attachments = files.getlist("workflow_attachment")
            filenames = [x.filename for x in workflow_attachments]
            return run["request"]["workflow_url"] in filenames
        return False

    def _create_run_stderr(self, run, filename, message):
        file_path = os.path.join(run["execution_path"], filename)
        with open(file_path, "w") as f:
            f.write("WESnake executor error: {}".format(message))
        return file_path

    def prepare_execution(self, run, files=[]):
        run["run_status"] = RunStatus.INITIALIZING.encode()

        # prepare run directory
        run_dir = os.path.abspath(os.path.join(self.datadir, run["run_id"]))
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
        run["execution_path"] = run_dir

        # check absolute workflow file exists and upload in case
        if self._check_workflow_files(run, files):
            if "workflow_attachment" in files:
                workflow_attachments = files.getlist("workflow_attachment")
                for attachment in workflow_attachments:
                    attachment.save(os.path.join(
                        run_dir, secure_filename(attachment.filename)))
        else:
            run["run_status"] = RunStatus.SYSTEM_ERROR.encode()
            run["run_log"]["stderr"] = self._create_run_stderr(
                run=run,
                filename="wesnake_run_stderr.txt",
                message=EXECUTOR_WF_NOT_FOUND)

        return run

    def execute(self, run):
        if not run["run_status"] == RunStatus.INITIALIZING.encode():
            return run

        # set workflow_url
        if os.path.isabs(run["request"]["workflow_url"]):
            workflow_url = run["request"]["workflow_url"]
        else:
            workflow_url = os.path.join(
                run["execution_path"],
                secure_filename(run["request"]["workflow_url"]))
        # execute run
        run_kwargs = {
            "snakefile": workflow_url,
            "workdir": run["execution_path"],
            "configfiles": [os.path.join(run["execution_path"], "config.yaml")]
        }
        run["start_time"] = get_current_time()
        run["run_log"]["cmd"] = ", ".join(
            "{}={}".format(key, run_kwargs[key]) for key in run_kwargs.keys()
        )
        task = run_snakemake.apply_async(
            args=[],
            kwargs={**run_kwargs, **self.kwargs})
        run["_celery_task_id"] = task.id
        return run
