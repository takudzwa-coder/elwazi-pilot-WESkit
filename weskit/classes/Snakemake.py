from weskit.classes.Run import Run
from weskit.tasks.snakemake import run_snakemake
from celery.task.control import revoke
from werkzeug.utils import secure_filename
from weskit.utils import get_current_time
from typing import Optional
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
    "QUEUED",
    "INITIALIZING",
    "RUNNING",
    "PAUSED"]

EXECUTOR_WF_NOT_FOUND = """
WESkit executor error: the workflow file was not found. Please provide either
a URL with a workflow file on the server or attach a workflow
via workflow_attachments."""


class Snakemake:
    def __init__(self, config: dict, datadir: str) -> None:
        self.kwargs = {}
        for parameter in (config["static_service_info"]
                                ["default_workflow_engine_parameters"]):
            self.kwargs[parameter["name"]] = eval(parameter["type"])(
                parameter["default_value"])
        self.datadir = datadir

    def cancel(self, run: Run) -> Run:
        revoke(run.celery_task_id, terminate=True, signal='SIGKILL')
        run.run_status = "CANCELED"
        return run

    def update_state(self, run: Run) -> Run:
        # check if task is running and update state
        if run.run_status in running_states:
            if run.celery_task_id is not None:
                running_task = run_snakemake.AsyncResult(run.celery_task_id)
                run.run_status = celery_to_wes_state[running_task.state]
            else:
                run.run_status = "UNKNOWN"
        return run

    def update_outputs(self, run: Run) -> Run:
        if run.run_status not in running_states:
            if run.celery_task_id is not None:
                running_task = run_snakemake.AsyncResult(run.celery_task_id)
                run.outputs["Snakemake"] = running_task.get()
        return run

    def update_runs(self, database, query) -> None:
        runs = database.get_runs(query)
        for run in runs:
            run = self.update_state(run)
            run = self.update_outputs(run)
            database.update_run(run)

    def create_and_insert_run(self, request, database) -> Optional[Run]:
        run = Run(data={"run_id": database._create_run_id(),
                        "run_status": "UNKNOWN",
                        "request_time": database.get_current_time(),
                        "request": request})
        if database.insert_run(run):
            return run
        else:
            return None

    def get_run(self, run_id, database, update) -> Run:
        if update:
            self.update_runs(database, query={"run_id": run_id})
        return database.get_run(run_id)

    def _run_has_url_of_valid_absolute_file(self, run):
        if os.path.isabs(run.request["workflow_url"]):
            if os.path.isfile(run.request["workflow_url"]):
                return True
        return False

    # check files, uploads and returns list of valid filesnames
    def _process_workflow_attachment(self, run, files):
        attachment_filenames = []
        if "workflow_attachment" in files:
            workflow_attachment_files = files.getlist("workflow_attachment")
            for attachment in workflow_attachment_files:
                filename = secure_filename(attachment.filename)
                # TODO could implement checks here
                attachment_filenames.append(filename)
                attachment.save(os.path.join(run.execution_path, filename))
        return attachment_filenames

    def _create_run_executions_logfile(self, run, filename, message):
        file_path = os.path.join(run.execution_path, filename)
        with open(file_path, "w") as f:
            f.write("WESkit executor error: {}".format(message))
        return file_path

    def prepare_execution(self, run, files=[]):
        run.run_status = "INITIALIZING"

        # prepare run directory
        run_dir = os.path.abspath(os.path.join(self.datadir, run.run_id))
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run.request["workflow_params"]), ff)
        run.execution_path = run_dir

        # process workflow attachment files
        attachment_filenames = self._process_workflow_attachment(run, files)

        # check for valid workflow_url
        if not (self._run_has_url_of_valid_absolute_file(run) or
                run.request["workflow_url"] in attachment_filenames):
            run.run_status = "SYSTEM_ERROR"
            run.outputs["execution"] = self._create_run_executions_logfile(
                run=run,
                filename="weskit_run_error.txt",
                message=EXECUTOR_WF_NOT_FOUND)

        return run

    def execute(self, run):
        if not run.run_status_check("INITIALIZING"):
            return run

        # set workflow_url
        if os.path.isabs(run.request["workflow_url"]):
            workflow_url = run.request["workflow_url"]
        else:
            workflow_url = os.path.join(
                run.execution_path,
                secure_filename(run.request["workflow_url"]))
        # execute run
        run_kwargs = {
            "snakefile": workflow_url,
            "workdir": run.execution_path,
            "configfiles": [os.path.join(run.execution_path, "config.yaml")]
        }
        run.start_time = get_current_time()
        run.run_log["cmd"] = ", ".join(
            "{}={}".format(key, run_kwargs[key]) for key in run_kwargs.keys()
        )
        task = run_snakemake.apply_async(
            args=[],
            kwargs={**run_kwargs, **self.kwargs})
        run.celery_task_id = task.id
        return run
