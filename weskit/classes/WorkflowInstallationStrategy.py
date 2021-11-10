#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from urllib.parse import urlparse

from trs_cli.client import TRSClient
from trs_cli.models import FileType

from weskit.ClientError import ClientError

T = TypeVar('T', bound='WorkflowInfo')


@dataclass
class WorkflowInfo:
    name: str
    version: str
    type: str

    @staticmethod
    def from_uri_string(uri: str, base_path: str = "ga4gh/trs/v2") -> T:
        """
        Take a TRS URI of the form trs://<server>:<port>/<base_path>/<id>/<version>/<type> and
        extract the individual components. This information uniquely identifies the workflow to be
        downloaded ind installed.
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
        name, version, type = rest

        # TRS-cli currently only supports non-plain types. Unfortunately, workflows may contain
        # binary data (FASTQs), which cannot be put directly into JSON responses from the TRS. This
        # means, for now we will only support workflows that contain only text files.
        if type not in ["SMK", "NXF"]:
            raise ClientError("Only 'SMK' and 'NFL' TRS workflow types are supported")

        return WorkflowInfo(name, version, type)


@dataclass
class WorkflowMetadata:
    """
    All information necessary to execute the workflow.
    """
    workflow_base: Path            # path to the workflow installation base directory
    primary_file: Path             # Absolute path to Snakefile, main.nf, etc.


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
               workflow_info.type

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


class TrsWorkflowInstaller(WorkflowInstallationStrategy):
    """
    Retrieve the workflow from a trusted tool repository service (TRS).
    """

    def __init__(self, workflow_base_dir: Path, trs_client: TRSClient):
        super(self).__init__(workflow_base_dir)
        self._trs_client = trs_client

    def _create_workflow_directory(self, workflow_info: WorkflowInfo):
        # TODO This will raise an error, if e.g. two workflow installations run in parallel, but
        #      at least thus it will prevent installation over an existing installation and
        #      corruption.
        self.get_workflow_directory(workflow_info).mkdir(exist_ok=False)

    def _install_workflow(self, workflow_info: WorkflowInfo):
        self._create_workflow_directory(workflow_info)
        files_by_type = self._trs_client.retrieve_files(
            out_dir=self.get_workflow_directory(workflow_info),
            type=workflow_info.type,
            id=workflow_info.name,
            version_id=workflow_info.version,
            is_encoded=False)   # TODO What should be here?
        if FileType.PRIMARY_DESCRIPTOR.value in files_by_type.keys():
            # TODO Check whether TRS allows e.g. Conda envs for the Snakemake process, or whatever
            #      to define e.g. the workflow manager version. For, new the primary file is
            #      sufficient.
            primary_files = files_by_type[FileType.PRIMARY_DESCRIPTOR.value]
            if len(primary_files) != 1:
                raise NotImplementedError(
                    "Cannot process workflows with more than one primary file yet")
            return WorkflowMetadata(primary_file=Path(primary_files[0]))
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
        relative_path_to_primary = \
            self.get_workflow_directory().relative_to(self._workflow_base_dir)
        return WorkflowMetadata(workflow_base=self._workflow_base_dir,
                                primary_file=relative_path_to_primary)

# TODO Tool aliases (check that the given URI is not just the same workflow but requested as alias
# TODO Maybe, run the tests for the tool after installation
