#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import os
import random
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TypeVar, Optional
from urllib.parse import urlparse

from flufl.lock import Lock
from trs_cli.client import TRSClient
from trs_cli.models import FileType

from weskit.ClientError import ClientError

logger = logging.Logger(__name__)

# Map the TRS types to WES workflow_types.
trs_type_to_workflow_type = {
    "SMK": "SMK",
    "NFL": "NFL",
    "PLAIN_SMK": "SMK",
    "PLAIN_NFL": "NFL"
}

T = TypeVar('T', bound='WorkflowInfo')


@dataclass
class WorkflowInfo:
    """
    Use factory method `WorkflowInfo.from_uri_string(uri)`

    name, version, type are the values extracted from the trs:// URI.
    workflow_type is the workflow type identifier as used by WES.
    server_uri is just the trs://server[:port] part.
    primary_file is the relative path to the primary workflow file (main.nf, etc.) extracted from
    the URI.
    """
    name: str
    version: str
    type: str
    workflow_type: str
    full_uri: str
    primary_file: Optional[Path] = None

    @staticmethod
    def from_uri_string(uri: str) -> T:
        """
        Take a TRS URI of the form

        trs://<server>:<port>/<id>/<version>/<type>/<primary_rel_path>

        and extract the individual components. This information uniquely identifies the workflow
        to be downloaded ind installed and essentially is mapped by the TRS to an HTTP request

        https://<server>:<port>/<base_path>/tools/<id>/versions/<version>/<type>/<primary_rel_path>

        The primary_rel_path is the path to the primary workflow file that will be used to execute
        the workflow. This may be, e.g. "main.nf" or "Snakefile".
        """
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme != "trs":
            raise ClientError(f"Invalid TRS URI. Not 'trs' scheme: '{uri}'")

        rest = list(filter(lambda v: len(v) > 0, parsed_uri.path.split("/")))
        if len(rest) < 3:
            raise ClientError("Invalid TRS URI. Remaining path components should be " +
                              f"id/version/type/[primary_path]: '{uri}'")
        name, version, type = rest[0:3]

        if len(rest) > 3:
            primary = Path(*rest[3:])
        else:
            primary = None

        # TRS-cli currently only supports non-plain types. Unfortunately, workflows may contain
        # binary data (FASTQs), which cannot be put directly into JSON responses from the TRS. This
        # means, for now we will only support workflows that contain only text files.
        if type not in trs_type_to_workflow_type.keys():
            raise ClientError(f"Unsupported workflow type '{type}'. Should be one of " +
                              ", ".join(trs_type_to_workflow_type.keys()))

        return WorkflowInfo(name, version, type,
                            full_uri=uri,
                            workflow_type=trs_type_to_workflow_type[type],
                            primary_file=primary)


class WorkflowMetadata:
    """
    All information necessary to execute the workflow.
    """

    def __init__(self, workflow_dir: Path, workflow_info: WorkflowInfo):
        """
        :param workflow_dir: Path to the workflow directory relative to the workflow base dir.
        :param workflow_info: WorkflowInfo object.
        """
        self._workflow_dir = workflow_dir
        self._workflow_info = workflow_info

    @property
    def workflow_dir(self):
        return self._workflow_dir

    @property
    def primary_file(self):
        return self._workflow_info.primary_file

    @property
    def name(self):
        return self._workflow_info.name

    @property
    def version(self):
        return self._workflow_info.version

    @property
    def trs_type(self):
        return self._workflow_info.type

    @property
    def wes_workflow_type(self):
        return self._workflow_info.workflow_type


class TrsWorkflowInstaller:
    """
    Retrieve the workflow from a trusted tool repository service (TRS).
    """

    def __init__(self,
                 trs_client: TRSClient,
                 workflow_base_dir: Path,
                 max_lock_time: timedelta = timedelta(minutes=3)):
        self._workflow_base_dir = workflow_base_dir
        self._trs_client = trs_client
        self._max_lock_time: timedelta = max_lock_time

    def _lockfile_name(self, workflow_dir: Path) -> Path:
        return workflow_dir.parent / (workflow_dir.name + ".lock")

    def _get_workflow_directory(self, workflow_info: WorkflowInfo) -> Path:
        return self._workflow_base_dir / \
               workflow_info.name / \
               workflow_info.version / \
               workflow_info.workflow_type

    def _workflow_is_installed(self, workflow_info: WorkflowInfo) -> bool:
        return self._get_workflow_directory(workflow_info).exists()

    def _install_workflow(self, workflow_info: WorkflowInfo):
        try:
            workflow_dir = self._get_workflow_directory(workflow_info)
            workflow_dir.mkdir(parents=True, exist_ok=False)
            files_by_type = self._trs_client.retrieve_files(
                out_dir=workflow_dir,
                type=workflow_info.type,
                id=workflow_info.name,
                version_id=workflow_info.version,
                is_encoded=False)   # TODO To decode or not to decode, that's the question!

            if FileType.PRIMARY_DESCRIPTOR.value in files_by_type.keys():
                primary_files = files_by_type[FileType.PRIMARY_DESCRIPTOR.value]
                if len(primary_files) != 1:
                    raise ClientError(f"Multiple primary files in '{workflow_info.full_uri}'. " +
                                      "Choose one of %s" % ", ".join(primary_files))
                elif workflow_info.primary_file is not None:
                    primary_file_rel = workflow_info.primary_file
                else:
                    primary_file_rel = primary_files[0]

                primary_file_abs = workflow_dir / primary_file_rel
                if not os.access(primary_file_abs):
                    # Installation-time check, that the primary file really was downloaded.
                    # It's more likely a client error than an NFS error, therefore report is as
                    # such.
                    raise ClientError("Could not access primary workflow file: " +
                                      f"'{primary_file_abs}'")

            elif FileType.CONTAINERFILE in files_by_type.keys():
                raise NotImplementedError(
                    "Cannot process container-based TRS workflows yet")
        except OSError as ex:
            message = f"Failed installing TRS workflow from '{workflow_info.full_uri}'"
            logger.warning(message, exc_info=ex)
            raise ClientError(message)

    def install(self, workflow_info: WorkflowInfo) -> WorkflowMetadata:
        """
        Get the information needed by the workflow management system to run the workflow. E.g.
        path to workflow main file (e.g. main.nf, Snakefile), conda environment for the workflow
        (e.g. for supplementary libraries), workflow manager version, etc.
        """
        workflow_dir_abs = self._get_workflow_directory(workflow_info)
        try:
            with Lock(lockfile=str(self._lockfile_name(workflow_dir_abs)),
                      lifetime=self._max_lock_time,
                      timeout=self._max_lock_time +
                      timedelta(seconds=random.randint(1, 30))):  # nosec b311
                # We always acquire a lock, when a workflow is requested. If it is already
                # installed, the lock will directly be released. Otherwise, one process acquires
                # the lock (even via NFS!) and the others wait till the workflow is installed. The
                # others, will either find the workflow successfully installed or retry the
                # installation, possibly with the same error. We leave it to the client not to
                # overload WESkit with senseless installation tries.
                #
                # The random timeout offset is to give the processes time to check whether the
                # directory exists.
                if not self._workflow_is_installed(workflow_info):
                    self._install_workflow(workflow_info)
        except TimeoutError:
            message = "Timed out when waiting for concurrent TRS workflow installations of " + \
                f"'{workflow_info.full_uri}'"
            logger.warning(message)
            raise ClientError(message)

        workflow_dir_rel = workflow_dir_abs.relative_to(self._workflow_base_dir)
        return WorkflowMetadata(workflow_dir=workflow_dir_rel,
                                workflow_info=workflow_info)
