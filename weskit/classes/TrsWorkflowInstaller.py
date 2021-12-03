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
from typing import TypeVar, Optional, List
from urllib.parse import urlparse
from zipfile import ZipFile, BadZipFile

from flufl.lock import Lock
from trs_cli.client import TRSClient
from trs_cli.errors import InvalidResponseError
from trs_cli.models import Error

from weskit.ClientError import ClientError

logger = logging.Logger(__name__)

# Map the TRS types to WESkit workflow engine identifiers.
trs_type_to_workflow_engine_id = {
    "SMK": "SMK",
    "NFL": "NFL",
    "PLAIN_SMK": "SMK",
    "PLAIN_NFL": "NFL"
}

T = TypeVar('T', bound='WorkflowInfo')


@dataclass
class WorkflowInfo:
    """
    Basically this is a parameter object for the `TrsWorkflowInstaller.install()` method. It is
    used in the return value that contains more metadata needed for the workflow execution.

    Use factory method `WorkflowInfo.from_uri_string(uri)`

    name, version, type are the values extracted from the trs:// URI.
    workflow_type is the workflow type identifier as used by WES.
    server_uri is just the trs://server[:port] part.
    primary_file is the relative path to the primary workflow file (main.nf, etc.) extracted from
    the URI.
    """
    server: str
    port: int
    name: str
    version: str
    type: str
    workflow_engine_id: str
    full_uri: str
    primary_file: Path

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
            raise ClientError("Invalid TRS URI. Scheme is " +
                              f"trs://host[:port]/id/version/type/[primary_path]: '{uri}'")
        name, version, type = rest[0:3]

        if len(rest) > 3:
            primary = Path(*rest[3:])
        else:
            raise ClientError(
                "Suffix your TRS URI with the relative path to the primary file")
            # primary: Optional[Path] = None

        if type not in trs_type_to_workflow_engine_id.keys():
            raise ClientError(f"Unsupported workflow type '{type}'. Should be one of " +
                              ", ".join(trs_type_to_workflow_engine_id.keys()))

        return WorkflowInfo(server=parsed_uri.hostname,
                            port=parsed_uri.port,
                            name=name,
                            version=version,
                            type=type,
                            full_uri=uri,
                            workflow_engine_id=trs_type_to_workflow_engine_id[type],
                            primary_file=primary)


class WorkflowInstallationMetadata:
    """
    All information about the workflow installation necessary to execute the workflow.
    """

    def __init__(self,
                 workflow_base_dir: Path,
                 workflow_dir: Path,
                 workflow_info: WorkflowInfo,
                 workflow_file: Optional[Path] = None):
        """
        :param workflow_dir: Path to the workflow directory relative to the workflow base dir.
        :param workflow_info: WorkflowInfo object created from the workflow URI.
        :param workflow_file: Path to workflow file to execute, relative to workflow_dir.
                              Defaults to primary file.
        """
        self._workflow_base_dir = workflow_base_dir
        self._workflow_dir = workflow_dir
        self._workflow_info = workflow_info
        if workflow_file is None:
            self._workflow_file = workflow_info.primary_file
        else:
            self._workflow_file = workflow_file

    @property
    def workflow_base_dir(self) -> Path:
        return self._workflow_base_dir

    @property
    def workflow_dir(self) -> Path:
        return self._workflow_dir

    @property
    def workflow_file(self) -> Path:
        return self._workflow_file

    @property
    def workflow_engine_id(self) -> str:
        return self._workflow_info.workflow_engine_id


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
        self.workflow_base_dir = workflow_base_dir
        self._trs_client = trs_client
        self._max_lock_time: timedelta = max_lock_time

    def _file_base_components(self, workflow_info: WorkflowInfo) -> List[str]:
        return [
            workflow_info.name,
            workflow_info.version,
            workflow_info.type,
            workflow_info.workflow_engine_id]

    def temporary_workflow_zip(self, workflow_info: WorkflowInfo) -> Path:
        return self.workflow_base_dir / \
               ".".join([*self._file_base_components(workflow_info), "zip"])

    def _lockfile_name(self, workflow_info: WorkflowInfo) -> Path:
        return self.workflow_base_dir / \
               ".".join([*self._file_base_components(workflow_info), "lock"])

    def _get_workflow_directory(self, workflow_info: WorkflowInfo) -> Path:
        return Path(self.workflow_base_dir, *self._file_base_components(workflow_info))

    def _workflow_is_installed(self, workflow_info: WorkflowInfo) -> bool:
        return self._get_workflow_directory(workflow_info).exists()

    def _install_workflow(self, workflow_info: WorkflowInfo) -> None:
        zip_file = self.temporary_workflow_zip(workflow_info)
        try:
            # Various response types possible (request.Response, Path (outfile), None, str,
            # requests.models.Response, ModelMetaclass, List[ModelMetaclass]). A perfect example
            # of why dynamic typing sucks.
            response = \
                self._trs_client.get_files(type=workflow_info.type,
                                           id=workflow_info.name,
                                           version_id=workflow_info.version,
                                           format="zip",
                                           outfile=zip_file)
            # We try to check for errors, but from the get_files() code it seems unclear, where
            # `Error` could be produced. Instead, `outfile` seems to be returned in case of errors.
            # Let's hope the exceptions cover the important cases and postpone changing TRS-cli
            # to later.
            if isinstance(response, Error):
                raise ClientError(f"Invalid response from {workflow_info.full_uri}: {response}")

            # Due to the uncertainties in the get_files() method, its call is isolated in a
            # dedicated try-except block.
        except ConnectionError as ex:
            message = f"Could not connect to TRS server {workflow_info.full_uri}"
            logger.error(message, exc_info=ex)
            raise ClientError(message)
        except InvalidResponseError as ex:
            message = "Could not validate TRS response. Server probably not supported."
            logger.warning(message, exc_info=ex)
            ClientError(message)
        except IOError as ex:
            logger.error(f"Could not write zip '{self.temporary_workflow_zip(workflow_info)}",
                         exc_info=ex)
            raise

        workflow_dir = self._get_workflow_directory(workflow_info)
        try:
            workflow_dir.mkdir(parents=True, exist_ok=False)
            with ZipFile(zip_file, 'r') as f:
                if str(workflow_info.primary_file) not in f.namelist():
                    logger.error(f"Checking {workflow_info.primary_file} in {f.namelist()}")
                    raise ClientError(f"Requested primary file '{workflow_info.primary_file}' " +
                                      "not in " + workflow_info.full_uri)
                f.extractall(workflow_dir)
        except BadZipFile as ex:
            message = f"Potentially bad zip file: {str(ex)}"
            logger.error(message, exc_info=ex)
            raise ClientError(message)
        finally:
            zip_file.unlink()

    def install(self, workflow_info: WorkflowInfo) -> WorkflowInstallationMetadata:
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

        workflow_dir_rel = workflow_dir_abs.relative_to(self.workflow_base_dir)
        return WorkflowInstallationMetadata(workflow_base_dir=self.workflow_base_dir,
                                            workflow_dir=workflow_dir_rel,
                                            workflow_info=workflow_info)
