# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging

import pytest

from test_utils import get_workflow_data

logger = logging.getLogger(__name__)


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoint that should be accessible without
    login are accessible.
    """
    @pytest.mark.integration
    def test_get_service_info(self, test_client_nologin):
        response = test_client_nologin.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200, response.json
        assert response.json["workflow_engine_versions"] == {
            "SMK": "7.30.2"
        }


class TestWithoutLogin:
    """
    The TestWithoutLogin class tests that endpoints are accessible without login
    and when login is deactivated.
    """
    @pytest.mark.integration
    def test_list_runs_wo_login(self, test_client_nologin, celery_worker):
        data = get_workflow_data(
            snakefile="tests/wf1/Snakefile",
            config="tests/wf1/config.yaml")
        response = test_client_nologin.post("/ga4gh/wes/v1/runs", data=data,
                                            content_type="multipart/form-data")
        assert response.status_code == 200, response.data
        response = test_client_nologin.get("/ga4gh/wes/v1/runs")
        assert response.status_code == 200, response.data

    @pytest.mark.integration
    def test_list_runs_extended_wo_login(self, test_client_nologin, celery_worker):
        response = test_client_nologin.get("/weskit/v1/runs")
        assert response.status_code == 200, response.data

    @pytest.mark.integration
    def test_submit_workflow_wo_login(self, test_client_nologin, celery_worker):
        data = get_workflow_data(
            snakefile="tests/wf1/Snakefile",
            config="tests/wf1/config.yaml")
        response = test_client_nologin.post("/ga4gh/wes/v1/runs", data=data,
                                            content_type="multipart/form-data")
        assert response.status_code == 200, response.data

    @pytest.mark.integration
    def test_get_run_stage(self,
                           test_client_nologin):
        response = test_client_nologin.get("/weskit/v1/runs/nonExistingRun/status")
        assert response.status_code == 404, response.data
