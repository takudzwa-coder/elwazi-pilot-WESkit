def test_get_workflow_type_versions(service_info):
    workflow_type_versions = service_info.get_workflow_type_versions()
    assert workflow_type_versions == ["snakemake 5.8.2"]


def test_get_supported_wes_versions(service_info):
    supported_wes_versions = service_info.get_supported_wes_versions()
    assert supported_wes_versions == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    supported_filesystem_protocols = service_info.get_supported_filesystem_protocols()
    assert supported_filesystem_protocols == ["s3"]


def test_get_workflow_engine_versions(service_info):
    workflow_engine_versions = service_info.get_workflow_engine_versions()
    assert workflow_engine_versions == {"snakemake": "5.8.2"}


def test_get_default_workflow_engine_parameters(service_info):
    default_workflow_engine_parameters = service_info.get_default_workflow_engine_parameters()
    assert default_workflow_engine_parameters[0]["name"] == "null"
    assert default_workflow_engine_parameters[1]["parameter_type"] == "none"
    assert default_workflow_engine_parameters[2]["default_value"] == "nothing"


def test_get_contact_info_url(service_info):
    contact_info_url = service_info.get_contact_info_url()
    assert contact_info_url == "your@email.de"


def test_get_tags(service_info):
    tags = service_info.get_tags()
    assert tags == {}
