def test_get_workflow_type_versions(service_info_executor):
    workflow_type_versions = service_info_executor.get_workflow_type_versions()
    assert workflow_type_versions == "snakemake 5.8.2"


def test_get_supported_wes_versions(service_info_executor):
    supported_wes_versions = service_info_executor.get_supported_wes_versions()
    assert supported_wes_versions == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info_executor):
    supported_filesystem_protocols = service_info_executor.get_supported_filesystem_protocols()
    assert supported_filesystem_protocols == ["s3"]


def test_get_workflow_engine_versions(service_info_executor):
    workflow_engine_versions = service_info_executor.get_workflow_engine_versions()
    assert workflow_engine_versions == "snakemake 5.8.2"


def test_get_contact_info_url(service_info_executor):
    contact_info_url = service_info_executor.get_contact_info_url()
    assert contact_info_url == "your@email.de"


def test_get_tags(service_info_executor):
    tags = service_info_executor.get_tags()
    assert tags == {}
