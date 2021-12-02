#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import random
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TypeVar, Optional
from urllib.parse import urlparse
from zipfile import ZipFile

from flufl.lock import Lock
from requests import Response
from trs_cli.client import TRSClient
from trs_cli.errors import InvalidResponseError

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
            raise ClientError(
                "Please suffix your TRS URI with the relative path to the primary file")
            # primary = None

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
    Retrieve the workflow from a trusted tool repository service (TRS). Workflows are downloaded
    with the TRSClient (which is preconfigured with server and port) and stored into
    `workflow_base_dir`.
    """

    def __init__(self,
                 trs_client: TRSClient,
                 workflow_base_dir: Path,
                 max_lock_time: timedelta = timedelta(minutes=3)):
        self._workflow_base_dir = workflow_base_dir
        self._trs_client = trs_client
        self._max_lock_time: timedelta = max_lock_time

    def _tempzip_name(self, workflow_info: WorkflowInfo) -> Path:
        return self._workflow_base_dir / \
               f"{workflow_info.name}.{workflow_info.version}.{workflow_info.workflow_type}.zip"

    def _lockfile_name(self, workflow_info: WorkflowInfo) -> Path:
        return self._workflow_base_dir / \
               f"{workflow_info.name}.{workflow_info.version}.{workflow_info.workflow_type}.lock"

    def _get_workflow_directory(self, workflow_info: WorkflowInfo) -> Path:
        return self._workflow_base_dir / \
               workflow_info.name / \
               workflow_info.version / \
               workflow_info.workflow_type

    def _workflow_is_installed(self, workflow_info: WorkflowInfo) -> bool:
        return self._get_workflow_directory(workflow_info).exists()

    def _install_workflow(self, workflow_info: WorkflowInfo):
        zip_file = self._tempzip_name(workflow_info)
        try:
            response = self._trs_client.get_files(type=workflow_info.type,
                                                  id=workflow_info.name,
                                                  version_id=workflow_info.version,
                                                  format="zip",
                                                  outfile=zip_file)
            if isinstance(response, Response):
                raise ClientError(f"Invalid response from {workflow_info.full_uri}")

            workflow_dir = self._get_workflow_directory(workflow_info)
            workflow_dir.mkdir(parents=True, exist_ok=False)
            with ZipFile(zip_file, 'r') as f:
                if str(workflow_info.primary_file) not in f.namelist():
                    logger.error(f"Checking {workflow_info.primary_file} in {f.namelist()}")
                    raise ClientError(f"Primary file {workflow_info.primary_file} not in " +
                                      workflow_info.full_uri)
                f.extractall(workflow_dir)
        except ConnectionError as ex:
            message = f"Could not connect to TRS server {workflow_info.full_uri}"
            logger.error(message, exc_info=ex)
            raise ClientError(message)
        except InvalidResponseError as ex:
            message = "Could not validate TRS response. Server probably not supported."
            logger.warning(message, exc_info=ex)
            ClientError(message)
        except IOError as ex:
            logger.error(f"Could not write zip '{self._tempzip_name(workflow_info)}", exc_info=ex)
            raise
        finally:
            zip_file.unlink()

    def install(self, workflow_info: WorkflowInfo) -> WorkflowMetadata:
        """
        Get the information needed by the workflow management system to run the workflow. E.g.
        path to workflow main file (e.g. main.nf, Snakefile), conda environment for the workflow
        (e.g. for supplementary libraries), workflow manager version, etc.

        Note that the method is blocking.
        """
        workflow_dir_abs = self._get_workflow_directory(workflow_info)
        try:
            with Lock(lockfile=str(self._lockfile_name(workflow_info)),
                      lifetime=self._max_lock_time,
                      default_timeout=self._max_lock_time +
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
                    logger.warning(f"Trying install from '{workflow_info.full_uri}")
                    self._install_workflow(workflow_info)
        except TimeoutError:
            message = "Timed out when waiting for concurrent TRS workflow installations of " + \
                f"'{workflow_info.full_uri}'"
            logger.warning(message)
            raise ClientError(message)

        workflow_dir_rel = workflow_dir_abs.relative_to(self._workflow_base_dir)
        return WorkflowMetadata(workflow_dir=workflow_dir_rel,
                                workflow_info=workflow_info)
