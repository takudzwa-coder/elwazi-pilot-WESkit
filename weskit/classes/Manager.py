import json
import os
import yaml
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.tasks.workflow import run_workflow
from celery.task.control import revoke
from werkzeug.utils import secure_filename
from weskit.utils import get_current_timestamp
from typing import Optional

celery_to_wes_state = {
    "PENDING": RunStatus.QUEUED,
    "STARTED": RunStatus.RUNNING,
    "SUCCESS": RunStatus.COMPLETE,
    "FAILURE": RunStatus.EXECUTOR_ERROR,
    "RETRY": RunStatus.QUEUED,
    "REVOKED": RunStatus.CANCELED
}

running_states = [
    RunStatus.QUEUED,
    RunStatus.INITIALIZING,
    RunStatus.RUNNING,
    RunStatus.PAUSED
]

EXECUTOR_WF_NOT_FOUND = """
WESkit executor error: the workflow file was not found. Please provide either
a URL with a workflow file on the server or attach a workflow
via workflow_attachments."""


class Manager:

    def __init__(self, workflow_dict: dict, data_dir: str) -> None:
        self.workflow_dict = workflow_dict
        self.data_dir = data_dir

    def cancel(self, run: Run) -> Run:
        revoke(run.celery_task_id, terminate=True, signal='SIGKILL')
        run.run_status = RunStatus.CANCELED
        return run

    def update_state(self, run: Run) -> Run:
        # check if task is running and update state
        if run.run_status in running_states:
            if run.celery_task_id is not None:
                running_task = run_workflow.AsyncResult(run.celery_task_id)
                run.run_status = celery_to_wes_state[running_task.state]
            else:
                run.run_status = RunStatus.UNKNOWN
        return run

    def update_outputs(self, run: Run) -> Run:

        if run.run_status not in running_states:
            if run.celery_task_id is not None:
                running_task = run_workflow.AsyncResult(run.celery_task_id)
                run.outputs["Workflow"] = running_task.get()
        return run

    def update_run(self, run: Run) -> Run:
        return self.update_outputs(self.update_state(run))

    def update_runs(self, database, query) -> None:
        runs = database.get_runs(query)
        for run in runs:
            run = self.update_run(run)
            database.update_run(run)

    def create_and_insert_run(self, request, database) -> Optional[Run]:
        run = Run(data={"run_id": database._create_run_id(),
                        "run_status": "UNKNOWN",
                        "request_time": get_current_timestamp(),
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
        run.run_status = RunStatus.INITIALIZING

        # prepare run directory
        run_dir = os.path.abspath(os.path.join(self.data_dir,
                                               run.run_id[0:4],
                                               run.run_id))
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
            run.run_status = RunStatus.SYSTEM_ERROR
            run.outputs["execution"] = self._create_run_executions_logfile(
                run=run,
                filename="weskit_run_error.txt",
                message=EXECUTOR_WF_NOT_FOUND)

        return run

    def execute(self, run: Run) -> Run:
        if not run.run_status == RunStatus.INITIALIZING:
            return run

        # set workflow_url
        if os.path.isabs(run.request["workflow_url"]):
            workflow_url = run.request["workflow_url"]
        else:
            workflow_url = os.path.join(
                run.execution_path,
                secure_filename(run.request["workflow_url"]))

        # set workflow_type
        if run.request["workflow_type"] in self.workflow_dict:
            workflow_type = run.request["workflow_type"]
        else:
            raise Exception("Workflow type:'" +
                            run.request["workflow_type"] +
                            "' is not known.")

        # execute run
        run_kwargs = {
            "workflow_type": workflow_type,
            "workflow_path": workflow_url,
            "workdir": run.execution_path,
            "config_files": [os.path.join(run.execution_path, "config.yaml")]
        }
        run.start_time = get_current_timestamp()
        run.run_log["cmd"] = ", ".join(
            "{}={}".format(key, run_kwargs[key]) for key in run_kwargs.keys()
        )
        task = run_workflow.apply_async(
                args=[],
                kwargs={**run_kwargs,
                        **self.workflow_dict[workflow_type].workflow_kwargs})

        run.celery_task_id = task.id
        return run
