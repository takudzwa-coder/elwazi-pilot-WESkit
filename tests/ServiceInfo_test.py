def test_get_workflow_type_versions(service_info):
    assert service_info.get_workflow_type_versions() == {
        "snakemake": {"workflow_type_version": ["5"]},
        "nextflow": {"workflow_type_version": ["20"]}
    }


def test_get_supported_wes_versions(service_info):
    assert service_info.get_supported_wes_versions() == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    assert service_info.get_supported_filesystem_protocols() == ["s3", "posix"]


def test_get_workflow_engine_versions(service_info):
    assert service_info.get_workflow_engine_versions() == {
        "snakemake": "5.8.2",
        "nextflow": "20.10.0"
    }


def test_get_default_workflow_engine_parameters(service_info):
    default = service_info.get_default_workflow_engine_parameters()
    assert default[0]["name"] == "cores"
    assert default[0]["type"] == "int"
    assert default[0]["default_value"] == "1"
    assert len(default) == 2


def test_get_auth_instructions_url(service_info):
    assert service_info.get_auth_instructions_url() == "https://somewhere.org"


def test_get_contact_info_url(service_info):
    assert service_info.get_contact_info_url() == "your@email.de"


def test_get_tags(service_info):
    assert service_info.get_tags() == {"tag1": "value1", "tag2": "value2"}
