#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import time
import yaml
import os
import requests
import pytest
from flask import current_app

from tests.utils_test import get_workflow_data


logger = logging.getLogger(__name__)


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoint that should be accessible without
    login are accessible.
    """
    @pytest.mark.integration
    def test_get_service_info(self, test_client_nologin):
        response = test_client_nologin.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200


class TestWithoutLogin:
    """
    The TestWithoutLogin class tests that endpoints are accessible without login and when login is deactivated.
    """
    @pytest.mark.integration
    def test_list_runs_wo_login(self, test_client_nologin, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_client_nologin.post("/ga4gh/wes/v1/runs", json=data)
        response = test_client_nologin.get("/ga4gh/wes/v1/runs")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_list_runs_extended_wo_login(self, test_client_nologin, celery_worker):
        response = test_client_nologin.get("/weskit/v1/runs")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_submit_workflow_wo_login(self, test_client_nologin, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_client_nologin.post("/ga4gh/wes/v1/runs", json=data)
        assert response.status_code == 200
