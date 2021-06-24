#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import os
from urllib.parse import urlparse

import yaml
from celery import Celery, Task
from celery.app.control import Control

from weskit.ClientError import ClientError
from weskit.classes.ShellCommand import ShellCommand
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
        if run.status in running_states:
            run.status = RunStatus.CANCELING
            # This is a quickfix for executing the tests.
            # This might be a bad solution for multithreaded use-cases,
            # because the current working directory is touched.
            cwd = os.getcwd()
            Control(self.celery_app). \
                revoke(task_id=run.celery_task_id,
                       terminate=True,
                       signal='SIGKILL')
            os.chdir(cwd)
        elif run.status is RunStatus.INITIALIZING:
            run.status = RunStatus.SYSTEM_ERROR
        return run

    def update_state(self, run: Run) -> Run:
        """
        Check whether task is running, initializing or canceling and update state.
        """
        if run.status in running_states or \
           run.status == RunStatus.INITIALIZING or \
           run.status == RunStatus.CANCELING:
            if run.celery_task_id is not None:
                running_task = self._run_task.\
                    AsyncResult(run.celery_task_id)
                if ((run.status != RunStatus.CANCELING) or
                    (run.status == RunStatus.CANCELING and
                     running_task.state == "REVOKED")):
                    run.status = celery_to_wes_state[running_task.state]
            elif (run.status in running_states or
                  run.status == RunStatus.CANCELING):
                run.status = RunStatus.SYSTEM_ERROR
        return run

    def update_run_results(self, run: Run) -> Run:
        """
        For a run in COMPLETED state, update the Run with information from the Celery task.
        """
        if run.status == RunStatus.COMPLETE:   # Celery job succeeded
            running_task = self._run_task.AsyncResult(run.celery_task_id)
            result = running_task.get()
            run.outputs["workflow"] = result["output_files"]
            run.log = result

            run_dir_abs = os.path.join(self.data_dir, result["workdir"])
            if run.exit_code != -1:            # Command (in Celery job) was executed (maybe error)
                with open(os.path.join(run_dir_abs, result["stdout_file"]), "r") as f:
                    run.stdout = f.readlines()
                with open(os.path.join(run_dir_abs, result["stderr_file"]), "r") as f:
                    run.stderr = f.readlines()
        return run

    def update_run(self, run) -> Run:
        updated_run = self.update_run_results(self.update_state(run))
        self.database.update_run(updated_run)
        return updated_run

    def update_runs(self, query) -> List[Run]:
        runs = self.database.get_runs(query)
        return list(map(self.update_run, runs))

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
                attachment.save(os.path.join(self.data_dir, run.dir, filename))
        return attachment_filenames

    def _create_run_executions_logfile(self, run, message):
        file_path = os.path.join(self.data_dir, run.dir,
                                 ".weskit", get_current_timestamp(), "server.log")
        with open(file_path, "w") as f:
            f.write("WESkit executor error: {}".format(message))
        return file_path

    def _prepare_workflow_path(self,
                               run_dir: str,
                               url: str,
                               attachment_filenames: List[str]) \
            -> str:
        """
        Compose the path to the workflow from a relative "file:" URI or by (cached) downloading
        an "https://" URI. After the function call the workflow file is present in the work_dir.

        Attached files are extracted to the run directory. (TODO Caching?)

        * Absolute input file://-paths are forbidden (raises ValueError).
        * Relative input file://-paths are interpreted relative the run's work-dir, both, if they
          are found in the attachment and if they refer to a path in the system-wide
          workflows_base_dir.

        https://- and s3://- paths are not yet implemented.
        """
        workflow_url = urlparse(url)
        workflow_path_rel = None
        if workflow_url.scheme in ["file", '']:
            if os.path.isabs(workflow_url.path):
                raise ClientError("Absolute workflow_url forbidden " +
                                  "(should be validated already): '%s'" % url)
            elif workflow_url.path in attachment_filenames:
                # File has already been extracted to work-dir. The command is executed in the
                # work-dir as the current work-dir, so we take it as it is.
                workflow_path_rel = workflow_url.path
            else:
                workflow_path_rel = os.path.join(
                    os.path.relpath(self.workflows_base_dir, os.path.join(self.data_dir, run_dir)),
                    workflow_url.path)
        elif workflow_url.scheme == "https":
            # TODO Download the workflow with git clone. Use caching.
            # TODO Copy to run directory?
            raise ClientError("https:// workflow_url is not implemented")

        workflow_path_abs = os.path.join(self.data_dir, run_dir, workflow_path_rel)
        if not os.path.exists(workflow_path_abs):
            # Report only the relative path. Everything else is implementation detail.
            raise ClientError("Derived workflow path does not exist: '%s'" % workflow_path_rel)

        return workflow_path_rel

    def prepare_execution(self, run, files=[]):

        if not run.status == RunStatus.INITIALIZING:
            return run

        # Prepare run directory
        if self.require_workdir_tag:
            run.dir = run.request["tags"]["run_dir"]
        else:
            run.dir = os.path.join(run.id[0:4], run.id)

        run_dir_abs = os.path.abspath(os.path.join(self.data_dir, run.dir))
        if not os.path.exists(run_dir_abs):
            os.makedirs(run_dir_abs)

        with open(run_dir_abs + "/config.yaml", "w") as ff:
            yaml.dump(run.request["workflow_params"], ff)

        run.workflow_path = self._prepare_workflow_path(
            run.dir,
            run.request["workflow_url"],
            self._process_workflow_attachment(run, files))
        return run

    def execute(self, run: Run) -> Run:
        if not run.status == RunStatus.INITIALIZING:
            return run

        # Set workflow_type
        if run.request["workflow_type"] in self.workflow_engines.keys():
            workflow_type = run.request["workflow_type"]
        else:
            raise ClientError("Workflow type '" +
                              run.request["workflow_type"] +
                              "' is not known. Know " +
                              ", ".join(self.workflow_engines.keys()))

        # Set workflow type version
        if run.request["workflow_type_version"] in self.workflow_engines[workflow_type].keys():
            workflow_type_version = run.request["workflow_type_version"]
        else:
            raise ClientError("Workflow type version '" +
                              run.request["workflow_type_version"] +
                              "' is not known. Know " +
                              ", ".join(self.workflow_engines[workflow_type].keys()))

        # Execute run
        run_kwargs = {
            "workflow_path": run.workflow_path,
            "workdir": os.path.join(self.data_dir, run.dir),
            "config_files": ["config.yaml"],
            "workflow_engine_params": []
        }
        run.start_time = get_current_timestamp()
        command: ShellCommand = self.workflow_engines[workflow_type][workflow_type_version].\
            command(**run_kwargs)
        run.log["cmd"] = command.command
        run.log["env"] = command.environment
        if run.status == RunStatus.INITIALIZING:
            task = self._run_task.apply_async(
                args=[],
                kwargs={
                    "command": command.command,
                    "environment": command.environment,
                    "base_workdir": self.data_dir,
                    "sub_workdir": run.dir
                })
            run.celery_task_id = task.id

        return run
