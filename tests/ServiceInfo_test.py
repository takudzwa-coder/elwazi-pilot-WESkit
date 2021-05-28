#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import datetime
from unittest import TestCase

from weskit import create_validator


def test_validate_config(test_validation, test_config):
    config_errors = create_validator(test_validation)(test_config)
    assert not config_errors, config_errors


def test_get_id(service_info):
    assert service_info.id() == "weskit.api"


def test_get_name(service_info):
    assert service_info.name() == "WESkit"


def test_get_description(service_info):
    assert service_info.description() == "WESkit - A GA4GH Compliant Workflow Execution Server"


def test_get_type(service_info):
    assert service_info.type() == {
        "group": "weskit.api",
        "artifact": "registry.gitlab.com/one-touch-pipeline/weskit/api",
        "version": "1.0.0"
    }


def test_get_organization(service_info):
    assert service_info.organization() == {
        "name": "My Org",
        "url": "https://my.org"
    }


def test_documentation_url(service_info):
    assert service_info.documentation_url() == \
        "https://gitlab.com/one-touch-pipeline/weskit/documentation/-/wikis/home"


def test_created_at(service_info):
    assert service_info.created_at() == \
           datetime.datetime(2021, 6, 4, 12, 58, 19, tzinfo=datetime.timezone.utc)


def test_updated_at(service_info):
    assert service_info.updated_at() == \
           datetime.datetime(2021, 6, 4, 12, 58, 19, tzinfo=datetime.timezone.utc)


def test_environment(service_info):
    assert service_info.environment() == "development"


def test_version(service_info):
    assert service_info.version() == "0.0.0"


def test_get_workflow_type_versions(service_info):
    assert service_info.workflow_type_versions() == {
        "snakemake": {"workflow_type_version": ["5.8.2"]},
        "nextflow": {"workflow_type_version": ["20.10.0"]}
    }


def test_get_supported_wes_versions(service_info):
    assert service_info.supported_wes_versions() == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    assert service_info.supported_filesystem_protocols() == ["s3", "file"]


def test_get_workflow_engine_versions(service_info):
    assert service_info.workflow_engine_versions() == {
        "snakemake": ["5.8.2"],
        "nextflow": ["20.10.0"]
    }


def test_get_default_workflow_engine_parameters(service_info):
    default = service_info.default_workflow_engine_parameters()
    TestCase().assertDictEqual(default, {
        "snakemake": {
            "5.8.2": {
                "env": {
                    "SOME_VAR": "with value"
                },
                "command": [
                    {
                        "name": "cores",
                        "value": 1
                    }
                ]
            }
        },
        "nextflow": {
            "20.10.0": {
                "env": {
                    "NXF_OPTS": "-Xmx256m"
                },
                "command": [
                    {"name": "Djava.io.tmpdir=/tmp"}
                ],
                "run": [
                    {"name": "with-trace"},
                    {"name": "with-timeline"},
                    {"name": "with-dag"},
                    {"name": "with-report"}
                ]
            }
        }})


def test_get_auth_instructions_url(service_info):
    assert service_info.auth_instructions_url() == "https://somewhere.org"


def test_get_contact_url(service_info):
    assert service_info.contact_url() == "mailto:your@email.de"


def test_get_tags(service_info):
    assert service_info.tags() == {"tag1": "value1", "tag2": "value2"}
