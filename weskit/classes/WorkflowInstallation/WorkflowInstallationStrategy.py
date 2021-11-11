#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import os.path
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from urllib.parse import urlparse

from trs_cli.client import TRSClient
from trs_cli.models import FileType

from weskit.ClientError import ClientError

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
    primary_file is the relative path to the primary workflow file (main.nf, etc.) extracted from
    the URI.
    """
    name: str
    version: str
    type: str
    primary_file: Path
    workflow_type: str

    @staticmethod
    def from_uri_string(uri: str, base_path: str = "ga4gh/trs/v2") -> T:
        """
        Take a TRS URI of the form

        trs://<server>:<port>/<base_path>/<id>/<version>/<type>/<primary_rel_path>

        and extract the individual components. This information uniquely identifies the workflow
        to be downloaded ind installed and essentially is mapped by the TRS to an HTTP request

        http://<server>:<port>/<base_path>/tools/<id>/versions/<version>/<type>/<primary_rel_path>

        The primary_rel_path is the path to the primary workflow file that will be used to execute
        the workflow. This may be, e.g. "main.nf" or "Snakefile".
        """
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme != "trs":
            raise ClientError(f"Invalid TRS URI. Not 'trs' scheme: '{uri}'")
        if not parsed_uri.path.startswith(base_path):
            raise ClientError(f"Invalid TRS URI. Path should start with {base_path}: '{uri}'")
        rest = parsed_uri.path.split("/")[3:]
        if len(rest) != 3:
            raise ClientError("Invalid TRS URI. Remaining path components should be " +
                              f"id/version/type: '{uri}'")
        name, version, type, primary = rest

        # TRS-cli currently only supports non-plain types. Unfortunately, workflows may contain
        # binary data (FASTQs), which cannot be put directly into JSON responses from the TRS. This
        # means, for now we will only support workflows that contain only text files.
        if type not in trs_type_to_workflow_type.keys():
            raise ClientError(f"Unsupported workflow type '{type}'. Should be one of " +
                              ", ".join(trs_type_to_workflow_type.keys()))

        return WorkflowInfo(name, version, type, Path(*primary),
                            workflow_type=trs_type_to_workflow_type[type])


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


class WorkflowInstallationStrategy(metaclass=ABCMeta):
    """
    Given contextual information like specified during a run request (URI, authentication, etc.)
    obtain the workflow and install it in the workflow installation directory.
    """

    def __init__(self, workflow_base_dir: Path):
        self._workflow_base_dir = workflow_base_dir

    def get_workflow_directory(self, workflow_info: WorkflowInfo) -> Path:
        return self._workflow_base_dir / \
               workflow_info.name / \
               workflow_info.version / \
               workflow_info.workflow_type

    def workflow_is_installed(self, workflow_info: WorkflowInfo) -> bool:
        # TODO This does not tell anything about whether a workflow installation is currently
        #      ongoing. Concurrent workflow installations will and wrongly assume the workflow
        #      exists completely installed.
        return self.get_workflow_directory(workflow_info).exists()

    @abstractmethod
    def install(self, workflow_info: WorkflowInfo) -> Path:
        """
        Try to install the workflow. Raises an exception, if the installation fails.
        """
        pass


class ManualWorkflowInstallation(WorkflowInstallationStrategy):
    """
    Simply ensure the workflow is locally installed. No automatic installation is done. Also no
    testing of the correctness of the installation, which needs to be done manually as well.
    """

    # TODO Workflow directory should have same format as for TRS name/version/type.
    # TODO Require metadata file to be installed in the workflow directory. Load and store in DB.
    # TODO Consider not supporting updates for locally installed workflows. Create new version.
    # TODO Upon first usage, read the metadata file and store to DB. After that use DB value.

    def __init__(self, workflow_base_dir: Path):
        super(self).__init__(workflow_base_dir)

    def install(self, workflow_info: WorkflowInfo) -> Path:
        if self.workflow_is_installed(workflow_info):
            return self.get_workflow_directory(workflow_info)
        else:
            raise RuntimeError(f"Workflow is not installed: '{workflow_info}")


class AttachedWorkflowInstaller(WorkflowInstallationStrategy):
    """
    Unpack the workflow from the file attached to the WES runs POST request.
    """
    pass


class TrsWorkflowInstaller(WorkflowInstallationStrategy):
    """
    Retrieve the workflow from a trusted tool repository service (TRS).
    """

    def __init__(self, workflow_base_dir: Path, trs_client: TRSClient):
        super(self).__init__(workflow_base_dir)
        self._trs_client = trs_client

    def _create_workflow_directory(self, workflow_info: WorkflowInfo) -> Path:
        # TODO This will raise an error, if e.g. two workflow installations run in parallel, but
        #      at least thus it will prevent installation over an existing installation and
        #      the resulting corruption.
        workflow_dir = self.get_workflow_directory(workflow_info)
        workflow_dir.mkdir(exist_ok=False)
        return workflow_dir

    def _install_workflow(self, workflow_info: WorkflowInfo):
        workflow_dir = self._create_workflow_directory(workflow_info)
        files_by_type = self._trs_client.retrieve_files(
            out_dir=workflow_dir,
            type=workflow_info.type,
            id=workflow_info.name,
            version_id=workflow_info.version,
            is_encoded=False)   # TODO What should be here?

        if FileType.PRIMARY_DESCRIPTOR.value in files_by_type.keys():
            # TODO Check whether TRS allows e.g. Conda envs for the Snakemake process, or whatever
            #      to define e.g. the workflow manager version. For now the primary file is
            #      sufficient.
            primary_files = files_by_type[FileType.PRIMARY_DESCRIPTOR.value]
            if len(primary_files) != 1:
                raise NotImplementedError(
                    "Cannot process workflows with more than one primary file yet")

            primary_file_abs = workflow_dir / primary_files[0]
            if not os.path.exists(primary_file_abs):
                # Installation time check, that the primary file really was downloaded.
                raise RuntimeError(f"Primary workflow file does not exist: '{primary_file_abs}")

        elif FileType.CONTAINERFILE in files_by_type.keys():
            # TODO Pull the containers as singularity container into the workflow directory.
            # TODO How is the workflow actually started, if a container is pulled?
            raise NotImplementedError(
                "Cannot process container-based TRS workflows yet")

    def install(self, workflow_info: WorkflowInfo) -> WorkflowMetadata:
        """
        Get the information needed by the workflow management system to run the workflow. E.g.
        path to workflow main file (e.g. main.nf, Snakefile), conda environment for the workflow
        (e.g. for supplementary libraries), workflow manager version, etc.
        """
        if not self.workflow_is_installed(workflow_info):
            self._install_workflow(workflow_info)

        workflow_dir_rel = self.get_workflow_directory().relative_to(self._workflow_base_dir)
        return WorkflowMetadata(workflow_dir=workflow_dir_rel,
                                workflow_info=workflow_info)

# TODO Tool aliases (check that the given URI is not just the same workflow but requested as alias
# TODO Maybe, run the tests for the tool after installation
