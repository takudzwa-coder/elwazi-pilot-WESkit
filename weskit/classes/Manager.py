import logging
import os
from urllib.parse import urlparse

import yaml
from celery import Celery, Task
from celery.app.control import Control
from weskit.classes.Database import Database
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.tasks.CommandTask import run_command
from werkzeug.utils import secure_filename
from weskit.utils import get_current_timestamp
from typing import Optional, List


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
    RunStatus.RUNNING
]

EXECUTOR_WF_NOT_FOUND = """
WESkit executor error: the workflow file was not found. Please provide either
a URL with a workflow file on the server or attach a workflow
via workflow_attachments."""

EXECUTOR_WORKDIR_MISSING = """Workdir missing."""

logger = logging.getLogger(__name__)


class Manager:

    def __init__(self,
                 celery_app: Celery,
                 database: Database,
                 workflow_engines: dict,
                 data_dir: str,
                 workflows_base_dir: str,
                 require_workdir_tag: bool) -> None:
        self.workflow_engines = workflow_engines
        self.data_dir = data_dir
        self.celery_app = celery_app
        self.database = database
        self.workflows_base_dir = workflows_base_dir
        self.require_workdir_tag = require_workdir_tag
        # Register the relevant tasks with fully qualified name. The function needs to be static.
        self.celery_app.task(run_command)

    @property
    def _run_task(self) -> Task:
        return self.celery_app.tasks["weskit.tasks.CommandTask.run_command"]

    def cancel(self, run: Run) -> Run:
        """See https://docs.celeryproject.org/en/latest/userguide/workers.html
        TODO Consider persistent revokes.
        """
        if run.run_status in running_states:
            run.run_status = RunStatus.CANCELING
            # This is a quickfix for executing the tests.
            # This might be a bad solution for multithreaded use-cases,
            # because the current working directory is touched.
            cwd = os.getcwd()
            Control(self.celery_app). \
                revoke(task_id=run.celery_task_id,
                       terminate=True,
                       signal='SIGKILL')
            os.chdir(cwd)
        elif run.run_status is RunStatus.INITIALIZING:
            run.run_status = RunStatus.SYSTEM_ERROR
        return run

    def update_state(self, run: Run) -> Run:
        # check if task is running, initializing or canceling and update state
        if run.run_status in running_states or \
           run.run_status == RunStatus.INITIALIZING or \
           run.run_status == RunStatus.CANCELING:
            if run.celery_task_id is not None:
                running_task = self._run_task.\
                    AsyncResult(run.celery_task_id)
                if ((run.run_status != RunStatus.CANCELING) or
                    (run.run_status == RunStatus.CANCELING and
                     running_task.state == "REVOKED")):
                    run.run_status = celery_to_wes_state[running_task.state]
            elif (run.run_status in running_states or
                  run.run_status == RunStatus.CANCELING):
                run.run_status = RunStatus.SYSTEM_ERROR
        return run

    def update_outputs(self, run: Run) -> Run:

        if run.run_status == RunStatus.COMPLETE:
            running_task = self._run_task.AsyncResult(run.celery_task_id)
            run.outputs["Workflow"] = running_task.get()["output_files"]
        return run

    def update_run(self, run: Run) -> Run:
        return self.update_outputs(self.update_state(run))

    def update_runs(self, query) -> None:
        runs = self.database.get_runs(query)
        for run in runs:
            run = self.update_run(run)
            self.database.update_run(run)

    def create_and_insert_run(self, request, user)\
            -> Optional[Run]:
        run = Run(data={"run_id": self.database.create_run_id(),
                        "run_status": "INITIALIZING",
                        "request_time": get_current_timestamp(),
                        "request": request,
                        "user_id": user})
        if self.database.insert_run(run):
            return run
        else:
            return None

    def get_run(self, run_id, update) -> Run:
        if update:
            self.update_runs(query={"run_id": run_id})
        return self.database.get_run(run_id)

    # check files, uploads and returns list of valid filenames
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

    def _prepare_workflow_path(self,
                               work_dir: str,
                               url: str,
                               attachment_filenames: List[str]) \
            -> str:
        """Compose the path to the workflow from a relative "file:" URI or
        by (cached) downloading an "https://" URI.

        Attached files are extracted to the run directory. (TODO Caching?)
        Relative files are interpreted relative to self.workflow_base_dir.
        """
        workflow_url = urlparse(url)
        workflow_path = None
        if workflow_url.scheme in ["file", '']:
            if os.path.isabs(workflow_url.path):
                raise ValueError("Absolute workflow_url forbidden " +
                                 "(should be validated already): '%s'" % url)
            elif workflow_url.path in attachment_filenames:
                # File has already been extracted to work-dir.
                workflow_path = os.path.join(
                    work_dir,
                    workflow_url.path)
            else:
                workflow_path = os.path.join(
                    self.workflows_base_dir,
                    workflow_url.path)
        elif workflow_url.scheme == "https":
            # TODO Download the workflow with git clone. Use caching.
            # TODO Copy to run directory?
            raise NotImplementedError("workflow_url in https://")
        return workflow_path

    def prepare_execution(self, run, files=[]):

        if not run.run_status == RunStatus.INITIALIZING:
            return run

        # prepare run directory
        if self.require_workdir_tag:
            run_dir = os.path.abspath(os.path.join(
                self.data_dir, run.request["tags"]["run_dir"]))
        else:
            run_dir = os.path.abspath(
                os.path.join(self.data_dir, run.run_id[0:4], run.run_id))

        if not os.path.exists(run_dir):
            os.makedirs(run_dir)

        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(run.request["workflow_params"], ff)
        run.execution_path = run_dir

        # get workflow path from workflow_url
        try:
            workflow_path = self._prepare_workflow_path(
                run.execution_path,
                run.request["workflow_url"],
                self._process_workflow_attachment(run, files))
            if not os.path.exists(workflow_path):
                raise IOError("Workflow path does not exist: '%s'" %
                              workflow_path)
            run.workflow_path = workflow_path
        except Exception as e:
            logger.warning(e, stack_info=True, exc_info=True)
            run.run_status = RunStatus.SYSTEM_ERROR
            run.outputs["execution"] = self._create_run_executions_logfile(
                run=run,
                filename="weskit_run_error.txt",
                message=EXECUTOR_WF_NOT_FOUND)

        return run

    def execute(self, run: Run) -> Run:
        if not run.run_status == RunStatus.INITIALIZING:
            return run

        # set workflow_type
        if run.request["workflow_type"] in self.workflow_engines.keys():
            workflow_type = run.request["workflow_type"]
        else:
            raise ValueError("Workflow type:'" +
                             run.request["workflow_type"] +
                             "' is not known. Know " +
                             ", ".join(self.workflow_engines.keys()))

        # execute run
        run_kwargs = {
            "workflow_path": run.workflow_path,
            "workdir": run.execution_path,
            "config_files": [os.path.join(run.execution_path, "config.yaml")],
            "workflow_engine_params": []
        }
        run.start_time = get_current_timestamp()
        command: List[str] = self.workflow_engines[workflow_type].command(**run_kwargs)
        run.run_log["cmd"] = command
        if run.run_status == RunStatus.INITIALIZING:
            task = self._run_task.apply_async(
                args=[],
                kwargs={
                    "command": command,
                    "workdir": run.execution_path
                })
            run.celery_task_id = task.id

        return run
