#  Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from asyncio import AbstractEventLoop
from datetime import timedelta
from os import PathLike
from typing import Optional, List

import kubernetes
from kubernetes.client import ApiClient, ApiException, V1Job, V1JobSpec, V1PodFailurePolicyRule, V1PodTemplateSpec, \
    V1ObjectMeta, V1PodSpec, V1Container, V1ResourceRequirements, V1EnvVar, V1VolumeDevice, V1VolumeMount

from memory_units import Unit
from weskit.classes.ShellCommand import ShellCommand
from weskit.classes.executor.Executor import Executor, ExecutionSettings, ExecutedProcess, ExecutionStatus, \
    CommandResult
from weskit.classes.storage.StorageAccessor import StorageAccessor


class KubernetesExecutor(Executor):
    """
    Submit jobs as Kubernetes Jobs. All jobs are executed with the same volumes in the same
    namespace.
    """

    def __init__(self,
                 kubernetes_client: ApiClient,
                 namespace: str,
                 volume_devices: Optional[List[V1VolumeDevice]] = None,
                 volume_mounts: Optional[List[V1VolumeMount]] = None,
                 event_loop: Optional[AbstractEventLoop] = None,
                 # We set a default TTL for jobs after finish of 1 week.
                 ttl_seconds: int = 604800):
        super().__init__(event_loop)
        self._kubernetes_client: ApiClient = kubernetes_client
        self._namespace = namespace
        self._ttl_seconds = ttl_seconds
        if volume_devices is None:
            self._volume_devices = []
        else:
            self._volume_devices = volume_devices
        if volume_mounts is None:
            self._volume_mounts = []
        else:
            self._volume_mounts = volume_mounts

    @property
    def hostname(self) -> str:
        return self._kubernetes_client.configuration.host

    @staticmethod
    def _to_minutes(duration: timedelta) -> int:
        return int(duration.total_seconds() / 60)

    def execute(self,
                job_name: str,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[ExecutionSettings] = None,
                **kwargs) \
            -> ExecutedProcess:
        """
        Submit a command to the execution infrastructure.

        The execution settings and the command are translated by the Executor into a (job)
        submission command (or REST call) that is then executed for the submission.

        The return value is a representation of the executed process.

        We use Kubernetes Jobs to model these relatively short-running command executions.
        Jobs are restarted by default if the ExecutionSettings.max_retries is set to a value
        larger than 1.

        :param command: The command to be executed.
        :param stdout_file: A path to a file into which the standard output shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.o%J
        :param stderr_file: A path to a file into which the standard error shall be written.
                            This can be a file-pattern, e.g. for LSF /path/to/file.e%J
        :param stdin_file: A path to a file from which to take the process standard input.
        :param settings: Execution parameters on the execution infrastructure.
        :return: A representation of the executed command.
        """
        api_instance = kubernetes.client.BatchV1Api(self._kubernetes_client)
        limits = {}
        if settings.memory is not None:
            limits["memory"] = f"{settings.memory.to(Unit.KILO).value}Ki"
        if settings.cores is not None:
            limits["cpu"] = int(settings.cores * 1000) / 1000   # milliCPUs is the smallest unit
        spec = V1JobSpec(active_deadline_seconds=settings.walltime,
                         # There may be many jobs, so we set a generous default TTL.
                         ttl_seconds_after_finished=self._ttl_seconds,
                         # In principle allow for restarts. Leave it to the client to decide
                         # whether to set max_retries to zero.
                         pod_failure_policy=[V1PodFailurePolicyRule(action="Count")],
                         backoff_limit=settings.max_retries,
                         template=V1PodTemplateSpec(
                             metadata=V1ObjectMeta(
                                 # This is the pod name. We want to use the pre-defined identifier
                                 # for this, to facilitate restartability.
                                 name=settings.job_name,
                                 # The following information may not be relevant to Kubernetes,
                                 # but may turn out to be useful when working with the system.
                                 labels={
                                     "job_name": settings.job_name,
                                     "accountingName": settings.accounting_name,
                                     "group": settings.group,
                                     "queue": settings.queue,
                                     "weskit_executor": self.id
                                 },
                                 namespace=self._namespace
                             ),
                             spec=V1PodSpec(
                                 containers=[
                                     V1Container(
                                         # This is a single-container pod. We use a static name.
                                         name="process",
                                         image=settings.container_image,
                                         resources=V1ResourceRequirements(limits=limits),
                                         env=[V1EnvVar(name=var[0], value=var[1])
                                              for var in command.environment.items()],
                                         command=command.command,
                                         volume_mounts=self._volume_mounts,
                                         volume_devices=self._volume_devices
                                     )
                                 ],
                                 restart_policy="Never"
                             )
                         ))
        try:
            job: V1Job = api_instance.create_namespaced_job(self._namespace,
                                                            spec,
                                                            namespace=self._namespace)
        except ApiException as e:
            pass

    # It is not the responsibility of the ExecutedProcess to know how to query its status or
    # how to get killed by the executor, etc. Therefore, the ExecutedProcess is handed back to the
    # Executor for the following operations.

    def get_status(self, process: ExecutedProcess) -> ExecutionStatus:
        """
        Get the status of the process in the execution infrastructure. The `process.result` is not
        modified.
        """
        api_instance = kubernetes.client.BatchV1Api(self._kubernetes_client)
        try:
            job: V1Job = api_instance.read_namespaced_job_status(self._namespace,
                                                                 job_name,
                                                                 self._namespace)
        except ApiException as e:
            pass
        return job.

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        """
        Update the result of the executed process, if possible. If the status of the process is not
        in a finished state, this function updates to the intermediate results at the time of
        the query. The CommandResult may thus contain no exit code.
        """


    def kill(self, process: ExecutedProcess) -> bool:
        """
        Cancel the process named by the process_id. Note that the killing operation may fail.
        Furthermore, note that if the process cannot be killed because it does not exist (anymore)
        no exception is thrown. Instead, if the process could not be found, False is returned.
        This is to reduce unnecessary exceptions in the common case where a process ends between
        the last status check and the killing command. Finally, even though the killing itself
        may not be immediately effective, this method immediately returns after sending the kill
        signal.
        """
        api_instance = kubernetes.client.BatchV1Api(self._kubernetes_client)
        try:
            job: V1Job = api_instance.delete_namespaced_job(self._namespace,
                                                            ...)
        except ApiException as e:
            pass


    def wait_for(self, process: ExecutedProcess) -> CommandResult:
        """
        Wait for the executed process and return the CommandResult. The ExecutedProcess is updated
        with the most recent result object.
        """
        pass

    @property
    def storage(self) -> StorageAccessor:
        """
        With Kubernetes, the storage will be available as physical volume. The underlying storage
        implementation is irrelevant. The storage accessor only needs to be able to access the
        storage. E.g. if you have a volume claim satisfied by an NFS volume, and you can access
        the data there via SSH, no one hinders you to use an SshStorageAccessor.
        """
        pass
