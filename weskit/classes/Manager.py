#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
from typing import Optional, List
from urllib.parse import urlparse

import yaml
from celery import Celery, Task
from celery.app.control import Control
from celery.result import AsyncResult
from pymongo.errors import PyMongoError
from trs_cli.client import TRSClient
from werkzeug.datastructures import FileStorage, ImmutableMultiDict
from werkzeug.utils import secure_filename

from weskit.classes.Database import Database
from weskit.classes.Run import Run
from weskit.classes.RunStatus import RunStatus
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.TrsWorkflowInstaller \
    import TrsWorkflowInstaller, WorkflowInfo, WorkflowInstallationMetadata
from weskit.exceptions import ClientError, ConcurrentModificationError
from weskit.tasks.CommandTask import run_command
from weskit.utils import get_current_timestamp, return_pre_signed_url

logger = logging.getLogger(__name__)


class Manager:

    def __init__(self,
                 celery_app: Celery,
                 database: Database,
                 executor: Dict[str, Any],
                 workflow_engines: dict,
                 data_dir: str,
                 workflows_base_dir: str,
                 require_workdir_tag: bool) -> None:
        self.executor = executor
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
        """
        See https://docs.celeryproject.org/en/latest/userguide/workers.html
        See https://docs.celeryproject.org/en/stable/userguide/workers.html#revoke-revoking-tasks
        TODO Consider persistent revokes.
        TODO State is not written back to DB
        """
        raise NotImplementedError()
        if run.status.is_running:
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
            # We cannot yet cancel a run in the initializing state. Ignore the request!
            # TODO Try updating the state until it is RUNNING. Then cancel the RUNNING run.
            pass
        return run

    def _get_run_task(self, run: Run) -> Optional[AsyncResult]:
        celery_task = self._run_task.AsyncResult(run.celery_task_id)
        logger.debug("Run %s with state %s got Celery ID %s in Celery state '%s'" % (
            run.id, run.status, run.celery_task_id, celery_task.state))
        return celery_task

    def _update_run_results(self, run: Run, celery_task) -> Run:
        """
        For the semantics of Celery's built-in states, see

            https://docs.celeryq.dev/en/stable/userguide/tasks.html#built-in-states

        For a run with SUCCESSFUL Celery state, update the Run with information from the
        Celery task.
        """
        if celery_task.status == "SUCCESS":
            # The command itself may have failed, though, because run_command catches execution
            # errors of the command and lets the Celery job succeed.
            result = celery_task.get()
            if "WESKIT_S3_ENDPOINT" in os.environ:
                run.outputs["S3"] = [return_pre_signed_url(outfile=out, workdir=result["workdir"])
                                     for out in result["output_files"]]
            run.outputs["workflow"] = result["output_files"]
            run.log = result

            run_dir_abs = os.path.join(self.data_dir, result["workdir"])
            if run.exit_code != -1:     # Command (in Celery job) was executed (maybe error 0)
                # WARNING: Updates of > 4 mb can be slow with MongoDB.
                with open(os.path.join(run_dir_abs, result["stdout_file"]), "r") as f:
                    run.stdout = f.readlines()
                with open(os.path.join(run_dir_abs, result["stderr_file"]), "r") as f:
                    run.stderr = f.readlines()
            else:
                # run_command produces exit_code == -1 if there are technical errors during the
                # command execution (other than workflow engine errors; e.g. SSH connection).
                raise self._record_error(run,
                                         RuntimeError("Error during processing of '%s'" % run.id),
                                         RunStatus.SYSTEM_ERROR)

        run.status = RunStatus.from_celery_and_exit(celery_task.state, run.exit_code)
        return run

    def _record_error(self, run: Run,
                      exception: Exception,
                      new_state: RunStatus) -> Exception:
        """
        Take an exception, log it, set run.status to new_state, and try to store the
        updated Run in the database (e.g. will if this is e.g. DB connection exception).

        Return the exception to simplify usage as `raise self._record_error(...)`.
        """
        logger.error("%s during processing of run '%s'" % (new_state.name, run.id))
        run.status = new_state
        if not isinstance(exception, PyMongoError) and \
                not isinstance(exception, ConcurrentModificationError):
            # Assumption: Recovery has been tried before (e.g. in Database). A PyMongoError here
            # is non-recoverable. Thus, we should not try to write to the DB for PyMongoErrors.
            self.database.update_run(run, resolution_fun=Run.merge)
        return exception

    def update_run(self,
                   run: Run,
                   max_tries: int = 1) -> Run:
        """
        Given an old Run and a new Run (that may or may not differ from the old Run version),
        retrieve the status information from Celery and update the run. Then, if there is a change
        compared to the old Run, update the run in the database.
        """
        try:
            if run.celery_task_id is not None:
                celery_task = self._get_run_task(run)
                run = self._update_run_results(run, celery_task)

            elif run.status.is_running or run.status == RunStatus.CANCELING:
                raise self._record_error(
                    run,
                    RuntimeError(f"No Celery task ID for run {run.id} in status {run.status}"),
                    RunStatus.SYSTEM_ERROR)

        except FileNotFoundError as e:
            # This may happen, if the open()s fail, e.g. because the run directory was manually
            # deleted or is unavailable due to network problems.
            raise self._record_error(run, e, RunStatus.SYSTEM_ERROR)

        return self.database.update_run(run, Run.merge, max_tries)

    def update_runs(self,
                    run_id: Optional[str] = None,
                    max_tries: int = 1) -> List[Run]:
        # Generally updating finished runs does not make much sense and creates problems with
        # deleted runs. On the long run, with increasing numbers of runs there will also be
        # a performance problem when updating accumulated finished runs.
        query: dict
        if run_id is None:
            query = {"run_status": {"$not": {"$in": [state.name
                                                     for state in RunStatus.TERMINAL_STATES()]}}}
        else:
            query = {"run_id": run_id}

        runs = self.database.get_runs(query)
        return list(map(lambda run: self.update_run(run, max_tries), runs))

    def create_and_insert_run(self, request, user_id)\
            -> Optional[Run]:

        request["workflow_params"] = json.loads(request["workflow_params"])

        if "workflow_engine_parameters" in request.keys():
            request["workflow_engine_parameters"] = \
                json.loads(request["workflow_engine_parameters"])

        if "tags" in request.keys():
            request["tags"] = json.loads(request["tags"])
        else:
            request["tags"] = None

        run = Run(data={"run_id": self.database.create_run_id(),
                        "run_status": RunStatus.INITIALIZING.name,
                        "request_time": get_current_timestamp(),
                        "request": request,
                        "user_id": user_id})
        self.database.insert_run(run)
        return run

    def get_run(self, run_id: str) -> Optional[Run]:
        """
        Request the current version of the run from the database. No update of the state
        from Celery is done. Return None, if no Run with the run_id can be found in the DB.
        """
        return self.database.get_run(run_id)

    # check files, uploads and returns list of valid filenames
    def _process_workflow_attachment(self, run,
                                     files: "Optional[ImmutableMultiDict[str, FileStorage]]"):
        attachment_filenames = []
        if files is not None and "workflow_attachment" in files:
            workflow_attachment_files = files.getlist("workflow_attachment")
            for attachment in workflow_attachment_files:
                if attachment.filename is None:
                    raise ClientError("Attachment file without name")
                else:
                    filename = secure_filename(attachment.filename)
                    # TODO could implement checks here
                    attachment_filenames.append(filename)
                    attachment.save(os.path.join(self.data_dir, run.dir, filename))
        return attachment_filenames

    def _prepare_workflow_path(self,
                               run_dir: str,
                               url: str,
                               attachment_filenames: List[str]) \
            -> str:
        """
        After the call either the workflow is accessible via the returned path relative to the
        run directory (could go outside the WESKIT_DATA base directory, e.g. for centrally
        installed workflows, or an exception is raised.

        The call may install the workflow. TODO This may block. Make workflow installation async?

        Attached files are extracted to the run directory.

        * Absolute input file://-paths are forbidden (raises ValueError).
        * Relative input file://-paths are interpreted relative the run's work-dir, both, if they
          are found in the attachment and if they refer to a path in the system-wide
          workflows_base_dir.
        * Absolute trs://-URIs

        """
        workflow_url = urlparse(url)
        workflow_path_rel: str
        if workflow_url.scheme in ["file", '']:
            # TODO Should we enforce the name/version/type structure also for manual workflows?
            if os.path.isabs(workflow_url.path):
                raise ClientError("Absolute workflow_url forbidden " +
                                  "(should be validated already): '%s'" % url)
            elif workflow_url.path in attachment_filenames:
                # File should already be extracted to work-dir. The command is executed in the
                # work-dir as the current work-dir, so we take it as it is.
                workflow_path_rel = secure_filename(workflow_url.path)

            else:
                # The file refers to an already installed workflow.
                workflow_path_rel = os.path.join(
                    os.path.relpath(self.workflows_base_dir, os.path.join(self.data_dir, run_dir)),
                    workflow_url.path)

        elif workflow_url.scheme == "https":
            raise ClientError("https:// workflow_url is not implemented")

        elif workflow_url.scheme == "trs":
            workflow_info = WorkflowInfo.from_uri_string(url)
            installer = TrsWorkflowInstaller(
                trs_client=TRSClient(uri=f"trs://{workflow_url.hostname}",
                                     port=workflow_url.port),
                workflow_base_dir=Path(self.workflows_base_dir))

            workflow_meta: WorkflowInstallationMetadata = installer.install(workflow_info)
            # TODO Is this what we want, installing TRS workflows centrally, for all users?
            workflow_path_rel = os.path.relpath(
                os.path.join(self.workflows_base_dir,
                             workflow_meta.workflow_dir,
                             workflow_meta.workflow_file),
                os.path.join(self.data_dir, run_dir))

        else:
            raise ClientError(f"Unknown scheme in workflow_url: '{url}'")

        # workflow_path_rel is always relative to the run_dir, even when referring to a centrally
        # installed workflow.
        workflow_path_abs = os.path.join(self.data_dir, run_dir, workflow_path_rel)
        if not os.path.exists(workflow_path_abs):
            raise ClientError("Derived workflow path is not accessible: '%s'" % workflow_path_abs)

        return workflow_path_rel

    def prepare_execution(self, run,
                          files: "Optional[ImmutableMultiDict[str, FileStorage]]" = None):
        if files is None:
            files = ImmutableMultiDict()

        if run.status != RunStatus.INITIALIZING:
            ex = RuntimeError("run.status not INITIALIZING but %s" % run.status)
            raise self._record_error(run, ex, RunStatus.SYSTEM_ERROR)

        # Prepare run directory
        if self.require_workdir_tag:
            run.dir = run.request["tags"]["run_dir"]
        else:
            run.dir = os.path.join(run.id[0:4], run.id)

        try:
            run_dir_abs = os.path.abspath(os.path.join(self.data_dir, run.dir))
            if not os.path.exists(run_dir_abs):
                os.makedirs(run_dir_abs, exist_ok=True)

            with open(run_dir_abs + "/config.yaml", "w") as ff:
                yaml.dump(run.request["workflow_params"], ff)

            run.workflow_path = self._prepare_workflow_path(
                run.dir,
                run.request["workflow_url"],
                self._process_workflow_attachment(run, files))
        except (ClientError, OSError) as e:
            # Any error during preparation, also if caused by the client should result in the
            # run to be in SYSTEM_ERROR state.
            raise self._record_error(run, e, RunStatus.SYSTEM_ERROR)

        return run

    def execute(self, run: Run) -> Run:
        if run.status != RunStatus.INITIALIZING:
            ex = RuntimeError("run.status not INITIALIZING but %s" % run.status)
            self._record_error(run, ex, RunStatus.SYSTEM_ERROR)
            raise ex

        # Set workflow_type
        if run.request["workflow_type"] in self.workflow_engines.keys():
            workflow_type = run.request["workflow_type"]
        else:
            # This should have been found in the validation.
            raise self._record_error(
                run,
                RuntimeError("Workflow type '%s' is not known. Know %s" %
                             (run.request["workflow_type"],
                              ", ".join(self.workflow_engines.keys()))),
                RunStatus.SYSTEM_ERROR)

        # Set workflow type version
        if run.request["workflow_type_version"] in self.workflow_engines[workflow_type].keys():
            workflow_type_version = run.request["workflow_type_version"]
        else:
            # This should have been found in the validation.
            raise self._record_error(
                run,
                RuntimeError("Workflow type version '%s' is not known. Know %s" %
                             (run.request["workflow_type_version"],
                              ", ".join(self.workflow_engines[workflow_type].keys()))),
                RunStatus.SYSTEM_ERROR)

        if run.workflow_path is None:
            raise self._record_error(run,
                                     RuntimeError(f"Workflow path of run is None: {run.id}"),
                                     RunStatus.SYSTEM_ERROR)

        # Execute run
        command: ShellCommand = self.workflow_engines[workflow_type][workflow_type_version].\
            command(workflow_path=run.workflow_path,
                    workdir=Path(self.data_dir, str(run.dir)),
                    config_files=[Path("config.yaml")],
                    engine_params=run.request.get("workflow_engine_parameters", {}))
        run.log["cmd"] = command.command
        run.log["env"] = command.environment
        run.start_time = get_current_timestamp()
        task = self._run_task.apply_async(
            args=[],
            kwargs={
                "command": command.command,
                "environment": command.environment,
                "local_base_workdir": self.data_dir,
                "sub_workdir": run.dir,
                "executor_parameters": self.executor
            })
        run.celery_task_id = task.id

        return run
