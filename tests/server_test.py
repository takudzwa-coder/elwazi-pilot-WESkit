#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import time
import os
import requests
import pytest
from flask import current_app

from weskit.classes.RunStatus import RunStatus
from tests.utils import \
    assert_within_timeout, is_within_timout, assert_status_is_not_failed, get_workflow_data
from weskit.utils import to_filename

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_run(test_client,
             celery_session_worker):
    """
    This fixture creates a mock runs as working state for accessing workflow results via the API.
    The tests will use the REST interface, but to circumvent authentication issues here, the
    run is created manually and the user_id is fixed to the value from the test keycloak DB.
    """
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf1/Snakefile",
        config="tests/wf1/config.yaml")
    run = manager.create_and_insert_run(request=request,
                                        user="6bd12400-6fc4-402c-9180-83bddbc30526")
    run = manager.prepare_execution(run)
    manager.database.update_run(run)
    run = manager.execute(run)
    manager.database.update_run(run)
    success = False
    start_time = time.time()
    while not success:
        assert_within_timeout(start_time)
        status = run.run_status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = current_app.manager.update_run(run)
            continue
        success = True
    assert os.path.isfile(os.path.join(run.execution_path, "hello_world.txt"))
    assert "hello_world.txt" in to_filename(run.outputs["workflow"])
    yield run


@pytest.fixture(name="OIDC_credentials", scope="session")
def login_fixture():
    """
    This fixture connects to a keycloak server requests an access token and
    returns a LoginClass object with the the following values:

    The access token which can be used as cookie.
    The header token which is the word "Bearer: " + access token
    The session token which is a specific value of the access token and is used for CSRF protection

    "OIDC_credentials" must be declared in the test function call to access this object.
    :return:
    OIDC_credentials.access_token
    OIDC_credentials.session_token
    OIDC_credentials.headerToken
    """

    class LoginClass:
        def __init__(self):
            payload = {
                "grant_type": "password",
                "username": "test",
                "password": "test",
                "client_id": "OTP",
                "client_secret": "7670fd00-9318-44c2-bda3-1a1d2743492d"
            }

            r2 = requests.post(
                url=current_app.oidc_login.token_endpoint,
                data=payload
            ).json()

            self.access_token = r2.get('access_token', "None2")
            self.session_token = {"X-Csrf-Token": r2.get('session_state', "None2")}
            self.headerToken = {'Authorization': 'Bearer %s' % self.access_token}

    return LoginClass()


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoint that should be accessible without
    login are accessible.
    """
    @pytest.mark.integration
    def test_get_service_info(self, test_client):
        response = test_client.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200, response.json


class TestWithoutLogin:
    """
    The TestWithoutLogin class ensures that all secured endpoints are not accessible without
    credentials.
    """
    @pytest.mark.integration
    def test_list_runs_wo_login(self, test_client):
        response = test_client.get("/ga4gh/wes/v1/runs")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_list_runs_extended_wo_login(self, test_client):
        response = test_client.get("/weskit/v1/runs")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_get_run_stderr_wo_login(self, test_client):
        response = test_client.get("/weskit/v1/runs/test_runId/stderr")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_get_run_stdout_wo_login(self, test_client):
        response = test_client.get("/weskit/v1/runs/test_runId/stdout")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_submit_workflow_wo_login(self, test_client):
        data = get_workflow_data(
            snakefile="file:tests/wf1/Snakefile",
            config="tests/wf1/config.yaml")
        response = test_client.post("/ga4gh/wes/v1/runs", json=data)
        assert response.status_code == 401


class TestWithHeaderToken:
    """
    The TestWithHeaderToken class ensures that some protected endpoints are accessible by
    submitting an access token in the request header in the format
    "'Authorization': 'Bearer xxxxxxxxxxxxxxxx-xxxx-xxxxxxxxxx"
    """

    @pytest.mark.integration
    def test_accept_run_workflow_header(self,
                                        test_client,
                                        test_run,
                                        OIDC_credentials):

        # test that outputs are relative
        response = test_client.get(
            "/ga4gh/wes/v1/runs/{}".format(test_run.run_id),
            headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        for output in response.json["outputs"]["workflow"]:
            assert not os.path.isabs(output)

    @pytest.mark.integration
    def test_accept_get_runs_header(self,
                                    test_client,
                                    test_run,
                                    OIDC_credentials):
        response = test_client.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert len([x for x in response.json if x['run_id'] == test_run.run_id]) == 1

    @pytest.mark.integration
    def test_list_runs_extended_with_header(self,
                                            test_client,
                                            test_run,
                                            OIDC_credentials):
        response = test_client.get("/weskit/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert len([x for x in response.json if x['run_id'] == test_run.run_id]) == 1

    @pytest.mark.integration
    def test_get_run_stderr_with_header(self,
                                        test_client,
                                        test_run,
                                        OIDC_credentials):
        run_id = test_run.run_id
        response = test_client.get(f"/weskit/v1/runs/{run_id}/stderr",
                                   headers=OIDC_credentials.headerToken)
        start_time = time.time()
        while response.status_code == 409:   # workflow still running
            assert is_within_timout(start_time, 20), "Timeout requesting stderr"
            time.sleep(1)
            response = test_client.get(f"/weskit/v1/runs/{run_id}/stderr",
                                       headers=OIDC_credentials.headerToken)

        assert response.status_code == 200, response.json
        assert isinstance(response.json, dict)
        assert "content" in response.json

    @pytest.mark.integration
    def test_get_run_stdout_with_header(self,
                                        test_client,
                                        test_run,
                                        OIDC_credentials):
        run_id = test_run.run_id
        response = test_client.get(f"/weskit/v1/runs/{run_id}/stdout",
                                   headers=OIDC_credentials.headerToken)
        start_time = time.time()
        while response.status_code == 409:    # workflow still running
            assert is_within_timout(start_time, 20), "Timeout requesting stdout"
            time.sleep(1)
            response = test_client.get(f"/weskit/v1/runs/{run_id}/stdout",
                                       headers=OIDC_credentials.headerToken)

        assert response.status_code == 200, response.json
        assert isinstance(response.json, dict)
        assert "content" in response.json
