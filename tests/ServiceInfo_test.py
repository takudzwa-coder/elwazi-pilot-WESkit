#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from unittest import TestCase

from weskit.utils import create_validator


def test_validate_config(test_validation, test_config):
    validation_result = create_validator(test_validation)(test_config)
    assert isinstance(validation_result, dict), validation_result

    # Ensure default value is set
    max_memory = list(filter(lambda p: p["name"] == "max-memory",
                             validation_result["workflow_engines"]
                             ["NFL"]["22.10.0"]["default_parameters"]))[0]
    assert "api" in max_memory
    assert not max_memory["api"]


# def test_get_id(service_info):
#     assert service_info.id() == "weskit.api"
#
#
# def test_get_name(service_info):
#     assert service_info.name() == "WESkit"
#
#
# def test_get_description(service_info):
#     assert service_info.description() == "WESkit - A GA4GH Compliant Workflow Execution Server"
#
#
# def test_get_type(service_info):
#     assert service_info.type() == {
#         "group": "weskit.api",
#         "artifact": "registry.gitlab.com/one-touch-pipeline/weskit/api",
#         "version": "1.0.0"
#     }
#
#
# def test_get_organization(service_info):
#     assert service_info.organization() == {
#         "name": "My Org",
#         "url": "https://my.org"
#     }
#
#
# def test_documentation_url(service_info):
#     assert service_info.documentation_url() == \
#         "https://gitlab.com/one-touch-pipeline/weskit/documentation/"
#
#
# def test_created_at(service_info):
#     assert service_info.created_at() == \
#            datetime.datetime(2021, 6, 4, 12, 58, 19, tzinfo=datetime.timezone.utc)
#
#
# def test_updated_at(service_info):
#     assert service_info.updated_at() == \
#            datetime.datetime(2021, 6, 4, 12, 58, 19, tzinfo=datetime.timezone.utc)
#
#
# def test_environment(service_info):
#     assert service_info.environment() == "development"
#
#
# def test_version(service_info):
#     assert service_info.version() == "0.0.0"


def test_get_workflow_type_versions(service_info):
    assert service_info.workflow_type_versions() == {
        "SMK": {"workflow_type_version": ["6.10.0"]},
        "NFL": {"workflow_type_version": ["22.10.0"]}
    }


def test_get_supported_wes_versions(service_info):
    assert service_info.supported_wes_versions() == ["1.0.0"]


def test_get_supported_filesystem_protocols(service_info):
    assert service_info.supported_filesystem_protocols() == ["file", "S3"]


def test_get_workflow_engine_versions(service_info):
    assert service_info.workflow_engine_versions() == {
        "SMK": "6.10.0",
        "NFL": "22.10.0"
    }


def test_get_default_workflow_engine_parameters(service_info):
    observed = service_info.default_workflow_engine_parameters()
    case = TestCase()
    case.maxDiff = None
    expected = [
        {"name": "SMK|6.10.0|engine-environment",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "SMK|6.10.0|max-memory",
         "default_value": "100m",
         "type": "Optional[str validFor Python.memory_units.Memory.from_str($)]"},
        {"name": "SMK|6.10.0|max-runtime",
         "default_value": "05:00",
         "type": "Optional[str validFor Python.tempora.parse_timedelta($)]"},
        {"name": "SMK|6.10.0|accounting-name",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "SMK|6.10.0|job-name",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "SMK|6.10.0|group",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "SMK|6.10.0|queue",
         "default_value": None,
         "type": "Optional[str]"},

        {"name": "NFL|22.10.0|accounting-name",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "NFL|22.10.0|job-name",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "NFL|22.10.0|group",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "NFL|22.10.0|queue",
         "default_value": None,
         "type": "Optional[str]"},
        {"name": "NFL|22.10.0|trace",
         "default_value": "true",
         "type": "bool"},
        {"name": "NFL|22.10.0|timeline",
         "default_value": "true",
         "type": "bool"},
        {"name": "NFL|22.10.0|graph",
         "default_value": "true",
         "type": "bool"},
        {"name": "NFL|22.10.0|report",
         "default_value": "true",
         "type": "bool"}
    ]
    observed.sort(key=lambda e: e["name"])
    expected.sort(key=lambda e: e["name"])
    case.assertListEqual(observed, expected)


def test_get_auth_instructions_url(service_info):
    assert service_info.auth_instructions_url() == "https://somewhere.org"


def test_get_contact_url(service_info):
    assert service_info.contact_url() == "mailto:your@email.de"


def test_get_tags(service_info):
    assert service_info.tags() == {"tag1": "value1", "tag2": "value2"}
