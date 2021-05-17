#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import os

import pytest
import yaml

from weskit.utils import create_validator
from weskit.classes.RunRequestValidator import RunRequestValidator


@pytest.fixture(scope="session")
def request_validation():
    request_validation_config = \
        os.path.join("config", "request-validation.yaml")
    with open(request_validation_config, "r") as yaml_file:
        request_validation = yaml.load(yaml_file, Loader=yaml.FullLoader)
    return request_validation


@pytest.fixture(scope="session")
def run_request_validator(request_validation):
    return RunRequestValidator(create_validator(request_validation["run_request"]))


def request(**kwargs):
    default = {
        "workflow_params": {},
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": "file:tests/wf/Snakefile"
    }
    return {**default, **kwargs}


def test_validate_success(run_request_validator):
    the_request = request()
    assert run_request_validator.validate(the_request, False) == []


def test_validate_structure(run_request_validator):
    assert run_request_validator.validate(request(workflow_params=""), False) == \
           [{'workflow_params': ['must be of dict type']}]

    request_wo_params = request()
    request_wo_params.pop("workflow_params")
    assert run_request_validator.validate(request_wo_params, False) == \
           [{'workflow_params': ['required field']}]

    request_wo_type = request()
    request_wo_type.pop("workflow_type")
    assert run_request_validator.validate(request_wo_type, False) == \
           [{'workflow_type': ['required field']}]

    request_wo_version = request()
    request_wo_version.pop("workflow_type_version")
    assert run_request_validator.validate(request_wo_version, False) == \
           [{'workflow_type_version': ['required field']}]

    request_wo_url = request()
    request_wo_url.pop("workflow_url")
    assert run_request_validator.validate(request_wo_url, False) == \
           [{'workflow_url': ['required field']}]


def test_validate_run_dir_tag(run_request_validator):
    assert run_request_validator.validate(request(tags={
        "run_dir": "file:relative/path/to/file"
    }), True) == []

    assert run_request_validator.validate(request(tags={
        "run_dir": "file:/absolute/path/to/file"
    }), True) == ["Not a relative path: 'file:/absolute/path/to/file'"]


def test_workflow_type(run_request_validator):
    assert run_request_validator.validate(request(workflow_type="snakemake"), False) == \
        []
    assert run_request_validator.validate(request(workflow_type="nextflow"), False) == \
        []
    assert run_request_validator.validate(request(workflow_type="blabla"), False) == \
        ["Unknown workflow_type 'blabla'. Know nextflow, snakemake"]


def test_workflow_type_version(run_request_validator):
    """Not implemented."""
    pass


def test_workflow_url(run_request_validator):
    assert run_request_validator.validate(request(workflow_url="relative/path"), False) == \
           []
    assert run_request_validator.validate(request(workflow_url="file:relative/path"), False) == \
           []
    assert run_request_validator.validate(request(workflow_url="file:/absolute/path"), False) == \
           ["Not a relative path: 'file:/absolute/path'"]
    assert run_request_validator.validate(request(workflow_url="/absolute/path"), False) == \
           ["Not a relative path: '/absolute/path'"]


def test_multiple_validations(run_request_validator):
    assert run_request_validator.validate(request(
        workflow_url="/absolute/path",
    ), True) == \
           ["Not a relative path: '/absolute/path'",
            "'run_dir' tag is required and tags field is missing"]
