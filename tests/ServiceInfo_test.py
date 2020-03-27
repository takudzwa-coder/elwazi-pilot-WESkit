def test_get_workflow_type_versions(service_info):
    assert service_info.get_workflow_type_versions() == ["snakemake 5.8.2"]


def test_get_supported_wes_versions(service_info):
    assert service_info.get_supported_wes_versions() == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    assert service_info.get_supported_filesystem_protocols() == ["s3"]


def test_get_workflow_engine_versions(service_info):
    assert service_info.get_workflow_engine_versions() == {"snakemake": "5.8.2"}


def test_get_default_workflow_engine_parameters(service_info):
    default_workflow_engine_parameters = service_info.get_default_workflow_engine_parameters()
    assert default_workflow_engine_parameters[0]["name"] == "null"
    assert default_workflow_engine_parameters[1]["parameter_type"] == "none"
    assert default_workflow_engine_parameters[2]["default_value"] == "nothing"


def test_get_auth_instructions_url(service_info):
    assert service_info.get_auth_instructions_url() == "null"


def test_get_contact_info_url(service_info):
    assert service_info.get_contact_info_url() == "your@email.de"


def test_get_tags(service_info):
    assert service_info.get_tags() == {}
