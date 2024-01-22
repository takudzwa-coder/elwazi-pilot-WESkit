# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path

import pytest
import yaml

from weskit.api.RunRequestValidator import RunRequestValidator
from weskit.utils import create_validator

from werkzeug.datastructures import FileStorage, ImmutableMultiDict


@pytest.fixture(scope="session")
def request_validation():
    request_validation_config = \
        os.path.join("config", "request-validation.yaml")
    with open(request_validation_config, "r") as yaml_file:
        request_validation = yaml.load(yaml_file, Loader=yaml.FullLoader)
    return request_validation


@pytest.fixture(scope="session")
def run_request_validator_rundir(request_validation, service_info):
    return RunRequestValidator(create_validator(request_validation["run_request"]),
                               service_info.workflow_engine_versions_dict(),
                               Path("test-data"),
                               True)


@pytest.fixture(scope="session")
def run_request_validator(request_validation, service_info):
    return RunRequestValidator(create_validator(request_validation["run_request"]),
                               service_info.workflow_engine_versions_dict(),
                               Path("test-data"),
                               False)


def request(**kwargs) -> dict:
    default = {
        "workflow_params": "{}",
        "workflow_type": "SMK",
        "workflow_type_version": "7.30.2",
        "workflow_url": "file:tests/wf/Snakefile"
    }
    return {**default, **kwargs}


def test_validate_success(run_request_validator):
    the_request = request()
    normalized = run_request_validator.validate(the_request)
    assert isinstance(normalized, dict), normalized


def test_validate_structure(run_request_validator):
    assert run_request_validator.validate(request(workflow_params={})) == \
           [{'workflow_params': ['must be of string type']},
            "workflow_params must be string with JSON dictionary"]

    request_wo_params = request()
    request_wo_params.pop("workflow_params")
    assert run_request_validator.validate(request_wo_params) == \
           [{'workflow_params': ['required field']}]

    request_wo_type = request()
    request_wo_type.pop("workflow_type")
    assert run_request_validator.validate(request_wo_type) == \
           [{'workflow_type': ['required field']}]

    request_wo_version = request()
    request_wo_version.pop("workflow_type_version")
    assert run_request_validator.validate(request_wo_version) == \
           [{'workflow_type_version': ['required field']}]

    request_wo_url = request()
    request_wo_url.pop("workflow_url")
    assert run_request_validator.validate(request_wo_url) == \
           [{'workflow_url': ['required field']}]

    request_with_trs = request(workflow_url="trs://some-server/ga4gh/trs/v2/wfid/wfvers/wftype")
    assert isinstance(run_request_validator.validate(request_with_trs), dict)


def test_validate_run_dir_tag(run_request_validator_rundir):
    assert isinstance(run_request_validator_rundir.validate(request(
        tags='{"run_dir": "file:relative/path/to/file"}')), dict)

    assert run_request_validator_rundir.validate(request(
        tags='{"run_dir": "file:/absolute/path/to/file"}')
        ) == ["Not a relative path: 'file:/absolute/path/to/file'"]


def test_workflow_type(run_request_validator):
    assert isinstance(run_request_validator.validate(request(workflow_type="SMK",
                                                             workflow_type_version="7.30.2")),
                      dict)
    assert isinstance(run_request_validator.validate(request(workflow_type="NFL",
                                                             workflow_type_version="23.04.1")),
                      dict)
    assert run_request_validator.validate(request(workflow_type="blabla")) == \
        ["Unknown workflow_type 'blabla'. Know NFL, SMK"]
    assert run_request_validator.validate(request(workflow_type="NFL",
                                                  workflow_type_version="blabla")) == \
        ["Unknown workflow_type_version 'blabla'. Know 23.04.1-singularity, 23.04.1"]


def test_workflow_type_version(run_request_validator):
    """Not implemented."""
    pass


def test_workflow_url(run_request_validator):
    assert isinstance(run_request_validator.validate(request(workflow_url="relative/path")),
                      dict)
    assert isinstance(run_request_validator.validate(request(workflow_url="file:relative/path")),
                      dict)
    assert run_request_validator.validate(request(workflow_url="file:/absolute/path")) == \
           ["Not a relative path: 'file:/absolute/path'"]
    assert run_request_validator.validate(request(workflow_url="/absolute/path")) == \
           ["Not a relative path: '/absolute/path'"]
    assert run_request_validator.validate(request(workflow_url="../outside")) == \
           ["Normalized path points outside allowed root: '../outside'"]
    assert run_request_validator.validate(request(workflow_url=12345))[1] == \
           "Could not parse URI '12345'"

    forbidden_uris = map(lambda c: "this%cforbidden" % c, "'\"(){}[]$")
    # Note: No scheme ("file") is provided. The error message does not contain them. Whether the
    #       URI contains the scheme is nothing of particular interest here, and simply considered
    #       here.
    # Note: Semicolon ; is not tested, because urlparse splits on ;.
    for uri in forbidden_uris:
        assert run_request_validator.validate(request(workflow_url=uri)) == \
               ["Forbidden characters: '%s'" % uri]


def test_multiple_validations(run_request_validator_rundir):
    assert run_request_validator_rundir.validate(request(
        workflow_url="/absolute/path",
    )) == \
           ["Not a relative path: '/absolute/path'",
            "'run_dir' tag is required but tags field is missing"]


def test_validate_attachment(run_request_validator):
    with open(os.path.join(os.getcwd(), "tests/wf5/.Snakemake"), "rb") as fp1:
        wf_file1 = FileStorage(fp1)
        wf_file1.filename = os.path.basename(wf_file1.filename)
        files = ImmutableMultiDict({"workflow_attachment": [wf_file1]})
        assert run_request_validator.validate(request(workflow_attachment=files)) == \
            ["At least one attachment filename is forbidden. Forbidden are: .nextflow, .snakemake"]

    with open(os.path.join(os.getcwd(), "tests/wf5/allowed.txt"), "rb") as fp2:
        wf_file2 = FileStorage(fp2)
        wf_file2.filename = os.path.basename(wf_file2.filename)
        file = ImmutableMultiDict({"workflow_attachment": [wf_file2]})
        assert run_request_validator.validate_attachment(file) == []


def test_validate_workflow_params(run_request_validator):
    assert run_request_validator.validate(request(
        workflow_params=None
    )) == [{"workflow_params": ["null value not allowed"]}]
    assert run_request_validator.validate(request(
        workflow_params="wrong"
    )) == ["JSON parse-error in workflow_params: Expecting value"]
    assert run_request_validator.validate(request(
        workflow_params="[]"
    )) == ["workflow_params must be string with JSON dictionary"]

    assert run_request_validator.validate(request(
        workflow_params="{}"
    )) == {
        'workflow_params': '{}',
        'workflow_type': 'SMK',
        'workflow_type_version': '7.30.2',
        'workflow_url': 'file:tests/wf/Snakefile',
    }

    assert run_request_validator.validate(request(
        workflow_params='{"engine-environment": "bla"}'
    )) == {
        'workflow_params': '{"engine-environment": "bla"}',
        'workflow_type': 'SMK',
        'workflow_type_version': '7.30.2',
        'workflow_url': 'file:tests/wf/Snakefile',
    }
    assert run_request_validator.validate(request(
        workflow_params='{"engine-environment": []}'
    )) == {
        'workflow_params': '{"engine-environment": []}',
        'workflow_type': 'SMK',
        'workflow_type_version': '7.30.2',
        'workflow_url': 'file:tests/wf/Snakefile',
    }


def test_validate_workflow_engine_parameters(run_request_validator):
    assert run_request_validator.validate(request(
        workflow_params=None
    )) == [{"workflow_params": ["null value not allowed"]}]
    assert run_request_validator.validate(request(
        workflow_params="wrong"
    )) == ["JSON parse-error in workflow_params: Expecting value"]
    assert run_request_validator.validate(request(
        workflow_params="[]"
    )) == ["workflow_params must be string with JSON dictionary"]

    assert run_request_validator.validate(request(
        workflow_params="{}"
    )) == {
               'workflow_params': '{}',
               'workflow_type': 'SMK',
               'workflow_type_version': '7.30.2',
               'workflow_url': 'file:tests/wf/Snakefile',
           }

    assert run_request_validator.validate(request(
        workflow_params='{"engine-environment": "bla"}'
    )) == {
               'workflow_params': '{"engine-environment": "bla"}',
               'workflow_type': 'SMK',
               'workflow_type_version': '7.30.2',
               'workflow_url': 'file:tests/wf/Snakefile',
           }
    assert run_request_validator.validate(request(
        workflow_params='{"engine-environment": []}'
    )) == {
               'workflow_params': '{"engine-environment": []}',
               'workflow_type': 'SMK',
               'workflow_type_version': '7.30.2',
               'workflow_url': 'file:tests/wf/Snakefile',
           }


def test_bad_url(run_request_validator):
    assert run_request_validator._validate_url(url=12345) == ["Could not parse URI '12345'"]
    assert run_request_validator._validate_workflow_url(url=12345) == \
        ["Could not parse URI '12345'"]
    assert run_request_validator._validate_file_url_path(url=12345) == \
        ["Could not parse URI '12345'"]


def test_validate_invalid_run_id(run_request_validator):
    assert run_request_validator.invalid_run_id(run_id="test_id") == "UUID expected. Got: 'test_id'"


def test_validate_url_invalid_scheme(run_request_validator):
    assert run_request_validator.validate(request(workflow_url="ftp://example.com")) == \
        ["Only 'file:' (relative) and 'trs:' are allowed in workflow URIs: 'ftp://example.com'"]


def test_validate_rundir_tag_missing_run_dir(run_request_validator_rundir):
    assert run_request_validator_rundir.validate(request(tags='{}')) == \
        ["'run_dir' tag is required and missing"]
