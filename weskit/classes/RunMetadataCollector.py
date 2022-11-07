#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Set, Optional, Dict, Union, Tuple

from urllib3.util import Url

from weskit.classes.Run import Run
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.WorkflowEngine import WorkflowEngine
from weskit.classes.executor.Executor import CommandResult, Executor
from weskit.utils import format_timestamp, mop, head_option


class JobMetadata:
    """
    The metadata of the workload jobs that are sent off to the compute-infrastructure by the
    `WorkflowEngine`.
    """

    def __init__(self,
                 job_id: str,
                 stdout_url: Url,
                 stderr_url: Url):
        self._job_id = job_id
        self._stdout_url = stdout_url
        self._stderr_url = stderr_url

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def stdout_url(self) -> Url:
        return self._stdout_url

    @property
    def stderr_url(self) -> Url:
        return self._stderr_url


@dataclass
class RunMetadata:
    """
    The metadata of tho workflow run. Both JobMetadata and RunMetadata are stored in the database.
    """

    workdir: Url

    # A URL representing the location where the workflow engine was executed (inferred from the
    # used `Executor`).
    engine_executor_url: Url

    # A URL representing the location to which the engine has submitted the workload jobs
    # (configured for the workflow run).
    compute_url: Url

    start_time: datetime
    cmd: ShellCommand

    stdout_url: Url
    stderr_url: Url
    log_url: Url

    # Can be None if execution not finish
    end_time: Optional[datetime]
    exit_code: Optional[int]
    output_file_urls: Optional[List[Url]]

    job_metadata: Set[JobMetadata]

    @property
    def result_dict(self) -> Dict[str, Union[Optional[int], str, Optional[List[str]], Dict[str, str]]]:
        return {
            "start_time": format_timestamp(self.start_time),
            "cmd": [str(el) for el in self.cmd.command],
            "env": self.cmd.environment,
            "workdir": str(self.cmd.workdir),
            "stdout_url": str(self.stdout_url),
            "stderr_url": str(self.stderr_url),
            "log_url": str(self.log_url),
            "exit_code": self.exit_code,
            "end_time": mop(self.end_time, format_timestamp),
            "output_file_urls": mop(self.output_file_urls, lambda files: [str(v) for v in files])
        }

    def __iter__(self):
        for (k, v) in {
            "start_time": self.start_time,
            "cmd": self.cmd,
            "end_time": self.end_time,
            "exit_code": self.exit_code,
            "stdout_url": self.stdout_url,
            "stderr_url": self.stderr_url,
            "log_url": self.log_url,
            "output_file_urls": self.output_file_urls
        }.items():
            yield k, v


# Names/strings representing a localhost. Note that this includes the empty string.
_LOCALHOST_NAMES = [
    "",
    "localhost",
    "127.0.0.1",
    "::1",
    "0:0:0:0:0:0:0:1"
]


class RunMetadataCollector:
    """
    Collect information on a workflow run from the diverse objects influencing where and how which
    information can be found.

    Some assumptions:

    1. WESkit's containers share a POSIX filesystem for the run-directory that is mounted at
       the same path in all containers (WESKIT_DATA).
    2. If execution is done in an external cluster, then all data produced in the cluster will
       be located in the same place, e.g. a cluster-wide shared filesystem, or uploaded to the same
       S3 bucket.
    """

    def __init__(self,
                 run: Run,
                 result: CommandResult,
                 engine: WorkflowEngine,
                 executor: Executor):
        self._run = run
        self._command_result = result
        self._engine = engine
        self._executor = executor

    def _exit_code(self) -> int:
        """
        The exit code reported here is always an integer. Special cases, such as that the
        `CommandResult` is not set (None) -- in case of an error -- or some system error
        situations are returned as special values.

        -1: `CommandResult` not available, e.g. if the execution failed because of missing command
        -2: Abnormal situation that should not happen after wait_for(). This is a system error.
        """
        exit_code: int
        if self._command_result is None:
            # result may be None, if the execution failed because the command does not exist.
            exit_code = -1
        else:
            exit_code = self._command_result.status.code
            if exit_code is None:
                # result.status should not be None if wait_for() was run. Let's not terminate the
                # worker, but just return some exit code value that indicates a system error.
                exit_code = -2
        return exit_code

    def _collect_metadata_items(self) -> Set[Tuple[str, str]]:
        """
        The `WorkflowEngine` class knows how to interpret the `Run` and `CommandResult`s, e.g.
        for parsing the engines output files.
        """
        return self._engine.run_metadata(self._run, self._command_result)

    def _collect_job_metadata(self, job_ids) -> Set[JobMetadata]:
        """
        The metadata from the jobs may be available in different ways, e.g.

        * As files in the run directory in the shared filesystem in the WESkit containers.
        * As URLs in the output available from the `CommandResult`.
        * Some files may only be available by listing the output bucket in remote S3 storage
          configured for the specific run.
        * Some URLs may be composed based on the information in the configuration of WESkit and the
          run.
        """
        pass

    def compute_url(self, engine_derived_url: Optional[Url]) -> Url:
        """
        A representation of the compute-host, on which the workload jobs are executed.
        For instance,

        * Snakemake is executed locally and runs its workload jobs locally. In this case, the
          compute_url is the worker container.
        * Snakemake may have been configured to submit its workload jobs to a TES. In this case,
          the information about the compute-hosts is available in the output of Snakemake.
        * Snakemake may have run jobs locally, but itself was executed by an `LsfExecutor` on a
          remote host. This means, that also the jobs were executed remotely, namely on the node
          on which the LSF cluster executed the cluster job.

        In these examples, the execution is in a cluster/Celery, and usually the compute-node
        name, is actually irrelevant. Instead, the name of the head-node of the cluster should be
        returned, because it represents the whole cluster.
        """
        pass
        # if engine_derived_url is not None \
        #         and engine_derived_url.hostname not in _LOCALHOST_NAMES:
        #     return engine_derived_url
        # else:
        #     # If the address is a localhost or similar, then the compute's URL is just the
        #     # executor's URL.
        #     return self._executor.host_url

    def _data_workdir(self) -> Url:
        """
        The final location of the "workdir" that contains all output data files. This location is
        determined by

        * the WESkit configuration, e.g. if the engine is executed locally, but with a shared
          filesystem. Here, the outputs can be listed within the worker.
        * the data is exposed via MinIO/S3 in the WESkit deployment but not via NFS or similar.
          In this situation, we can predict the final URLs from the relative paths.
        * the workflow engine is configured to upload the results to some external storage, e.g. S3.
          In this case, the output URLs may be listed in the engine's output, but that is not 100%
          certain and may even depend on the upload code in the engine for the specific storage
          protocol.
        * the workload execution infrastructure to which the engine submits (e.g. TESK),
          automatically uploads the result data to some storage. In this case, the final location
          may be retrieved from the external infrastructure, e.g. via a REST interface.
        """
        pass

    def _log_workdir(self) -> Url:
        """
        This is the URL of the log files produced by the workflow engine. These can be e.g. the
        workload jobs's standard error and output, status files produced by the workflow engine,
        etc. Usually (assumption), the engine will not by itself upload its logs anywhere.
        Therefore, it depends only on the `Executor` as the executor determines where the engine
        process is started.
        """
        pass

    def _weskit_workdir(self) -> Url:
        """
        The location of WESkit's log files. This includes the stdout and stderr of the executed
        engine process, which the `Executor`s always

        WESkit`s working directory is always the run directory, to which also the attachment files
        are written.

        TODO Should the logs always remain with the engine-process and retrieved afterwards for parsing?
        """
        pass

        def _get_output_files(self) -> List[Url]:
            """
            Output files are always reported as paths relative to the run-directory. This is because
            the absolute location is the result of complex interactions between the WESkit configuration
            the `Executor` storage configuration, the `Executor` capabilities and configuration (e.g.
            CWL-TES that uploads the data to a fixed configured S3 bucket), the workflow engine
            configuration (e.g. workflow engine parameters, profiles) or even hardcoded in the
            workflow). Furthermore, it seems not to be possible to assume that all workflow engines
            report the absolute output location of their files (e.g. currently Snakemake reports just
            the relative locations if `--stats` is used).

            Therefore, a list of URLs with just paths relative to the run-directory is returned.

            Note that files in the `.weskit/` directory are not returned, but the log files specific
            to the workflow engine are reported.
            """
        # Collect files, but ignore those that are in the .weskit/ directory. They are tracked by
        # the fields in the execution log (or that of previous runs in this directory).
        return list(map(
            lambda path: Url(path=str(path)),
            filter(
                lambda fn: not Path(fn).is_relative_to(worker_context.log_base_subdir),  # type: ignore  # noqa
                collect_relative_paths_from(worker_context.workdir(workdir)))))          # type: ignore  # noqa

    def get(self) -> RunMetadata:
        # Compile raw metadata
        raw_metadata = self._collect_metadata_items()
        job_metadata = self._collect_job_metadata([job_md[1]
                                                   for job_md in raw_metadata
                                                   if job_md[0] == "job_id"])
        # Prepare output
        # TODO Use PathContext or come up with a new idea.
        log_dir = Path(".weskit", format_timestamp(self._command_result.start_time))
        return RunMetadata(start_time=self._command_result.start_time,
                           cmd=self._command_result.command,
                           weskit_workdir=Url(scheme="file",
                                              path=str(self._command_result.command.workdir)),
                           end_time=self._command_result.end_time,
                           exit_code=self._exit_code(),
                           engine_executor_url=self._command_result.executor.host_url,
                           compute_url=self.compute_url(
                               head_option(raw_metadata, lambda md: md[0] == "compute_url")),
                           terminal_workdir=self._get_terminal_workdir(),
                           log_url=Url(path=str(log_dir)),
                           stdout_url=Url(path=str(log_dir / "stdout.log")),
                           stderr_url=Url(path=str(log_dir / "stdout.log")),
                           output_file_urls=self._get_output_files(),
                           job_metadata=job_metadata)
