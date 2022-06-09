import shutil
from pathlib import Path
from typing import Optional, Union, List

import pytest
import requests
from trs_cli import TRSClient
from trs_cli.models import ToolFile, Error

from weskit.exceptions import ClientError
from weskit.classes.TrsWorkflowInstaller import \
    TrsWorkflowInstaller, WorkflowInfo, WorkflowInstallationMetadata


def test_workflow_info():
    trs_uri = 'trs://dev.workflowhub.eu:443/230/1/SMK/workflow/Snakefile'
    workflow_info = WorkflowInfo.from_uri_string(trs_uri)
    assert workflow_info.server == "dev.workflowhub.eu"
    assert workflow_info.port == 443
    assert workflow_info.workflow_engine_id == "SMK"
    assert workflow_info.primary_file == Path("workflow/Snakefile")
    assert workflow_info.name == "230"
    assert workflow_info.version == "1"

    trs_uri = 'trs://dev.workflowhub.eu/12345/3/NFL/main.nf'
    workflow_info = WorkflowInfo.from_uri_string(trs_uri)
    assert workflow_info.full_uri == trs_uri
    assert workflow_info.workflow_engine_id == "NFL"
    assert workflow_info.primary_file == Path("main.nf")
    assert workflow_info.name == "12345"
    assert workflow_info.version == "3"

    # CWL not supported yet.
    trs_uri = 'trs://dev.workflowhub.eu/54321/100/CWL/wf.cwl'
    with pytest.raises(ClientError) as e_info:
        WorkflowInfo.from_uri_string(trs_uri)
    assert e_info.value.message.startswith("Unsupported workflow type 'CWL'. Should be one of")

    # No primary file (currently needs to be provided, because its not yet retrieved from ro-crate)
    trs_uri = 'trs://dev.workflowhub.eu/54321/100/NFL/'
    with pytest.raises(ClientError) as e_info:
        WorkflowInfo.from_uri_string(trs_uri)
    assert e_info.value.message.startswith(
        "Suffix your TRS URI with the relative path to the primary file")

    # Not trs scheme
    trs_uri = 'https://dev.workflowhub.eu/54321/100/NFL/'
    with pytest.raises(ClientError) as e_info:
        WorkflowInfo.from_uri_string(trs_uri)
    assert e_info.value.message.startswith("Invalid TRS URI. Not 'trs' scheme:")

    # Incomplete TRS URI
    trs_uri = 'trs://dev.workflowhub.eu/54321/100/'
    with pytest.raises(ClientError) as e_info:
        WorkflowInfo.from_uri_string(trs_uri)
    assert e_info.value.message.startswith("Invalid TRS URI. Scheme is")


def test_workflow_installation_metadata():
    trs_uri = 'trs://dev.workflowhub.eu:443/230/1/SMK/workflow/Snakefile'
    workflow_info = WorkflowInfo.from_uri_string(trs_uri)
    wimd = WorkflowInstallationMetadata(
        Path("/path/to/base"),
        Path("path/to/workflow"),
        workflow_info)
    assert wimd.workflow_base_dir == Path("/path/to/base")
    assert wimd.workflow_engine_id == workflow_info.workflow_engine_id
    assert wimd.workflow_file == workflow_info.primary_file
    assert wimd.workflow_dir == Path("path/to/workflow")

    wimd = WorkflowInstallationMetadata(Path("/base/path"),
                                        Path("path/to/workflows"),
                                        workflow_info,
                                        Path("to/other/workflow/file"))
    assert wimd.workflow_file == Path("to/other/workflow/file")


class MockTRSClient(TRSClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_files(
            self,
            type: str,
            id: str,
            version_id: Optional[str] = None,
            format: Optional[str] = None,
            outfile: Optional[Path] = None,
            token: Optional[str] = None,
    ) -> Union[
        List[ToolFile],
        Error,
        Path,
        requests.models.Response,
    ]:
        pass  # Do nothing. We create the post-condition of get_files() externally.


@pytest.fixture(scope="function")   # Clean up tempdir after every test
def trs_installer(temporary_dir):
    mock_client = MockTRSClient(uri="https://dev.workflowhub.eu", port=443)
    yield TrsWorkflowInstaller(trs_client=mock_client,
                               workflow_base_dir=Path(temporary_dir))


def test_install(trs_installer):
    # Note that the URI contains the sub-directory to the primary workflow file to be executed.
    trs_uri = 'trs://dev.workflowhub.eu:443/1234/1/SMK/Snakefile'
    workflow_info = WorkflowInfo.from_uri_string(trs_uri)
    expected_zip_path = trs_installer.temporary_workflow_zip(workflow_info)
    shutil.copy(Path("tests/wf1.zip"), expected_zip_path)
    assert expected_zip_path.exists()

    result = trs_installer.install(workflow_info)
    assert not expected_zip_path.exists()
    assert not result.workflow_dir.is_absolute()
    assert (result.workflow_base_dir / result.workflow_dir).exists()
    assert (result.workflow_base_dir / result.workflow_dir / "Snakefile").exists()
    assert result.workflow_engine_id == "SMK"
