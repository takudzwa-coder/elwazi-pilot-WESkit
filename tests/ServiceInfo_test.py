def test_get_workflow_type_versions(service_info):
    assert service_info.get_workflow_type_versions() == ["snakemake 5.8.2"]


def test_get_supported_wes_versions(service_info):
    assert service_info.get_supported_wes_versions() == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    assert service_info.get_supported_filesystem_protocols() == ["s3", "posix"]


def test_get_workflow_engine_versions(service_info):
    assert service_info.get_workflow_engine_versions() == {"snakemake": "5.8.2"}


def test_get_default_workflow_engine_parameters(service_info):
    default_workflow_engine_parameters = service_info.get_default_workflow_engine_parameters()
    assert default_workflow_engine_parameters[0]["name"] == "null"
    assert default_workflow_engine_parameters[0]["parameter_type"] == "none"
    assert default_workflow_engine_parameters[0]["default_value"] == "nothing"


def test_get_auth_instructions_url(service_info):
    assert service_info.get_auth_instructions_url() == "https://somewhere.org"


def test_get_contact_info_url(service_info):
    assert service_info.get_contact_info_url() == "your@email.de"


def test_get_tags(service_info):
    assert service_info.get_tags() == { "tag1": "value1", "tag2": "value2" }


def test_get_system_state_counts(service_info):
    assert service_info.get_system_state_counts() == {
        "UNKNOWN": 0,
        "QUEUED": 0,
        "INITIALIZING": 0,
        "RUNNING": 0,
        "PAUSED": 0,
        "COMPLETE": 0,
        "EXECUTOR_ERROR": 0,
        "SYSTEM_ERROR": 0,
        "CANCELED": 0,
        "CANCELING": 0
    }