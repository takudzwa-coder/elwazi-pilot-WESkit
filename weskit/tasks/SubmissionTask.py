#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import json
import logging
import os
from abc import ABCMeta
from typing import Optional
from uuid import UUID

from weskit.tasks.BaseTask import BaseTask

from weskit.celery_app import celery_app
from weskit.classes.Run import Run
from weskit.classes.RunMetadataCollector import RunMetadataCollector, RunMetadata
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.WorkflowEngine import WorkflowEngine
from weskit.classes.executor.Executor import Executor, CommandResult, ProcessId
from weskit.utils import now

logger = logging.getLogger(__name__)


class SubmissionTask(BaseTask, metaclass=ABCMeta):

    def submit(self, run: Run) -> ProcessId:
        start_time = now()
        run.start_time = start_time

        # It's a bug to have workdir not defined here!
        command: ShellCommand = run.command
        if command.workdir is None:
            raise RuntimeError("No working directory defined for command: %s" % str(command))
        else:
            workdir = command.workdir

        run.execution_log["cmd"] = command.command
        run.execution_log["env"] = command.environment

        worker_context = run_workflow.worker_context
        executor_context = run_workflow.executor_context

        if run_workflow.executor_type.executes_engine_remotely:
            logger.info("Running command in {} (worker)/{} (command): {}".
                        format(worker_context.run_dir(command.workdir),
                               executor_context.run_dir(command.workdir),
                               [repr(el) for el in command.command]))
        else:
            if worker_context != executor_context:
                raise RuntimeError("No remote, but distinct remote path context: "
                                   f"{worker_context} != {executor_context}")
            logger.info("Running command in {} (worker): {}".
                        format(executor_context.run_dir(workdir),
                               [repr(el) for el in command.command]))

        worker_log_dir = worker_context.log_dir(workdir, start_time)
        executor_log_dir = executor_context.log_dir(workdir, start_time)

        result: Optional[CommandResult] = None
        try:
            logger.info("Uploading run-dir %s" % str(executor_log_dir))
            # We always upload the run-dir, even if it may already exist (e.g. if this Celery task was
            # interrupted and was restarted). Executors that use temporary storage need the upload for
            # every attempt. If the directory exists, then uploading it again won't hurt, unless the
            # configuration or attachment files were modified remotely.
            run_workflow.executor.storage.put(run.run_dir(run_workflow.worker_context),
                                              run.run_dir(run_workflow.executor_context),
                                              recursive=True,
                                              dirs_exist_ok=True)

            logger.info("Creating log-dir %s" % str(executor_log_dir))
            # For every execution attempt a new log-dir will be created (based on the timestamp).
            run_workflow.executor.storage.create_dir(executor_log_dir)

            if run_workflow.executor_type.executes_engine_locally or \
                    run_workflow.config["executor"]["login"]["hostname"] == "localhost":
                # A locally executing engine needs the local environment, e.g. for Conda.
                command.environment = {**dict(os.environ), **command.environment}

            process = \
                run_workflow.executor.execute(
                    command,
                    stdout_file=executor_context.stdout_file(workdir, start_time),
                    stderr_file=executor_context.stderr_file(workdir, start_time),
                    settings=run.execution_settings)

            # TODO For #157 the process information (process ID! job ID!, etc.) needs to be updated
            #      in the database, instead. No wait here then.
            result = run_workflow.executor.wait_for(process)

        finally:
            # TODO For #157 this code will go into the monitoring Celery task.
            run_workflow.executor.get(executor_log_dir,
                                      worker_log_dir,
                                      recursive=True,
                                      dirs_exist_ok=True)

            workflow_engine = run_workflow. \
                workflow_engines[run.request["workflow_type"]][run.request["workflow_type_version"]]

            metadata = RunMetadataCollector(run, result, workflow_engine, run_workflow.executor).get()
            execution_log = metadata.result_dict
            with open(worker_context.execution_log_file(workdir, start_time), "w") as fh:
                json.dump(execution_log, fh)
                print("\n", file=fh)
            with open(worker_context.execution_log_file(workdir, start_time), "w") as fh:
                json.dump(execution_log, fh)
                print("\n", file=fh)

        return execution_log

    def run_metadata(self, run: Run, engine: WorkflowEngine, executor: Executor) -> RunMetadata:
        """
        A workflow is assumed to create workload jobs, e.g. on a cluster. The access to the logs
        and output files depends on run's and the workflow engine's configuration and the
        capabilities of the compute-infrastructure (e.g. some REST service). It might even depend
        on the storage system. Some examples

        * The HTC storage may or may not be mounted as shared storage into the WESkit containers.
        * The engine may be configured to stage/unstage input/output files to S3.
        * The executor, e.g. TESK, may be stage/unstage inputs/outputs to S3.

        Also, there is a difference between the engine's log-files and the data files. E.g. if
        Snakemake is run locally in the container (`LocalExecutor`) but the run configured to
        submit to TESK, then the logs are local, while the data is on some external S3.

        This function integrates all available information and produces the final run metadata.
        """
        pass

    def finalize(self, run: Run) -> dict:
        pass


@celery_app.task(base=SubmissionTask)
def run_workflow(run_id: UUID):
    """
    Run a workflow in a working directory. The sub_workdir has to be a relative path, such that
    `base_workdir/sub_workdir` is the path in which the command is executed. base_workdir
    can be absolute or relative. For relative paths, the path will be in the active directory
    which can be either locally or remotely (e.g. the home directory after SSH login, whatever
    that may be).

    Write log files into a timestamp sub-directory of `sub_workdir/log_base`. There will be
    `stderr` and `stdout` files for the respective output of the command and `log.json` with
    general logging information, including the "command", "start_time", "end_time", and the
    "exit_code". Paths in the execution log are all relative.

    Returns a dict with fields "stdout_file", "stderr_file", "log_file" for the three log
    files, and "output_files" for all files created by the process, except the three log-files.
    All paths in the file will be relative to the base_workdir/sub_workdir (remote or local),
    except for the workdir, which is the relative path beneath the local_base_workdir directory
    (that should be the WESKIT_DATA directory).

    "exit_code" is set to negative values for system errors

      * -1: No result could be produced from the command, e.g. if a prior
            mkdir failed, or similar abnormal situations.
      * -2: The process was waited for without timeout, but no valid exit-code was produced
            (Executor.wait_for() should always result in an exit-code != None).
    """
    run = run_workflow.database.get_run(run_id)

    # We must not submit the same workflow Run twice at the same time into a cluster.
    process_id: Optional[ProcessId] = run_workflow.find_running_workflow(run)

    if process_id is None:
        # No running process found in executor. This means, at most a single process for the
        # workflow run will be active in the executor at a time.
        process_id = run_workflow.submit(run)

    return run_workflow.finalize(run, process_id)
