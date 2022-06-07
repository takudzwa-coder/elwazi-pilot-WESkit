#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import os
import time

import pytest
import requests
from flask import current_app
from validators.url import url as validate_url

from test_utils import \
    assert_within_timeout, is_within_timeout, assert_status_is_not_failed, get_workflow_data
from weskit import WESApp
from weskit.api.Helper import Helper
from weskit.classes.RunStatus import RunStatus
from weskit.oidc.User import User, not_logged_in_user_id
from weskit.utils import to_filename

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_run(test_client,
             celery_session_worker):
    """
    This fixture creates a mock run as working state for accessing workflow results via the API.
    The tests will use the REST interface, but to circumvent authentication issues here, the
    run is created manually and the user_id is fixed to the value from the test keycloak DB.
    """
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf1/Snakefile",
        config="tests/wf1/config.yaml")
    run = manager.create_and_insert_run(request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run = manager.prepare_execution(run)
    run = manager.execute(run)
    run = manager.database.update_run(run)
    success = False
    start_time = time.time()
    while not success:
        assert_within_timeout(start_time)
        status = run.status
        if status != RunStatus.COMPLETE:
            assert_status_is_not_failed(status)
            print("Waiting ... (status=%s)" % status.name)
            time.sleep(1)
            run = current_app.manager.update_run(run)
            continue
        success = True
    assert os.path.isfile(os.path.join(manager.data_dir, run.dir, "hello_world.txt"))
    assert "hello_world.txt" in to_filename(run.outputs["workflow"])
    yield run


@pytest.fixture(scope="module")
def incomplete_run(test_client,
                   celery_session_worker):
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf1/Snakefile",
        config="tests/wf2/config.yaml")
    run = manager.create_and_insert_run(request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run.request["workflow_params"]["duration"] = 1
    run = manager.prepare_execution(run)
    manager.database.update_run(run)
    return run


@pytest.fixture(scope="function")
def long_run(test_client,
             celery_session_worker):
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf2/Snakefile",
        config="tests/wf2/config.yaml")
    run = manager.create_and_insert_run(request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run.request["workflow_params"]["duration"] = 10
    run = manager.prepare_execution(run)
    run = manager.execute(run)
    run = manager.database.update_run(run)
    start_time = time.time()
    status = False
    while status != RunStatus.RUNNING:
        assert_within_timeout(start_time)
        status = run.status
        assert_status_is_not_failed(status)
        print("Waiting ... (status=%s)" % status.name)
        time.sleep(1)
        run = current_app.manager.update_run(run)
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


class TestHelper:

    @pytest.mark.integration
    def test_get_user_id(self, nologin_app: WESApp, login_app: WESApp):
        user = User(id="testUser")
        assert Helper(login_app, user).user.id == user.id
        assert Helper(nologin_app, None).user.id == not_logged_in_user_id

    @pytest.mark.integration
    def test_access_denied_response(self, login_app):
        user = User(id="testUser")
        helper = Helper(login_app, user)
        assert helper.get_access_denied_response("runId", None) == \
               ({"msg": "Could not find 'runId'",
                 "status_code": 404
                 }, 404)

        class Run:
            @property
            def id(self):
                return "runId"

            @property
            def user_id(self):
                return "Whatever"

        assert helper.get_access_denied_response("runId", Run()) == \
               ({"msg": "User 'testUser' not allowed to access 'runId'",
                 "status_code": 403
                 }, 403)

    @pytest.mark.integration
    def test_log_response(self, test_run, login_app):
        helper = Helper(login_app, User(id=test_run.user_id))
        stderr, stderr_code = helper.get_log_response(test_run.id, "stderr")
        assert stderr_code == 200
        assert stderr["content"][0] == 'Building DAG of jobs...\n'

        stdout, stdout_code = helper.get_log_response(test_run.id, "stdout")
        assert stdout_code == 200
        assert len(stdout["content"]) == 0

    @pytest.mark.integration
    def test_log_response_run_incomplete(self, incomplete_run, login_app):
        helper = Helper(login_app, User(id=incomplete_run.user_id))
        assert helper.get_log_response(incomplete_run.id, "stderr") == \
               ({"msg": "Run '%s' is not in COMPLETED state" % incomplete_run.id,
                 "status_code": 409
                 }, 409)

    @pytest.mark.integration
    def test_log_response_access_denied(self, test_run, login_app):
        helper = Helper(login_app, User(id="forbiddenUser"))
        assert helper.get_log_response(test_run.id, "stderr") == \
               ({"msg": f"User 'forbiddenUser' not allowed to access '{test_run.id}'",
                 "status_code": 403
                 }, 403)


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoints that should be accessible without
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
    def test_get_run_status(self, test_client):
        response = test_client.get("/weskit/v1/runs/test_runId/status")
        assert response.status_code == 404

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
    def test_submit_workflow_header_upload(self,
                                           test_client,
                                           test_run,
                                           OIDC_credentials):

        data = {}
        data["workflow_params"] = '{"text": "hello world"}'
        data["workflow_url"] = "Snakefile"
        data["workflow_type"] = "SMK"
        data["workflow_type_version"] = "6.10.0"
        data["workflow_attachment"] = (open("tests/wf1/Snakefile", "rb"), "Snakefile")
        data["workflow_engine_parameters"] = "{}"

        response = test_client.post(
            "/ga4gh/wes/v1/runs",
            data=data,
            content_type="multipart/form-data",
            headers=OIDC_credentials.headerToken)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_accept_run_workflow_header(self,
                                        test_client,
                                        test_run,
                                        OIDC_credentials):

        # test that outputs are relative
        response = test_client.get(
            "/ga4gh/wes/v1/runs/{}".format(test_run.id),
            headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        for output in response.json["outputs"]["workflow"]:
            assert not os.path.isabs(output)
        # test that s3 outputs are valid urls
        for output_url in response.json["outputs"]["S3"]:
            assert validate_url(output_url)

    @pytest.mark.integration
    def test_accept_get_runs_header(self,
                                    test_client,
                                    test_run,
                                    OIDC_credentials):
        response = test_client.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert len([x for x in response.json if x['run_id'] == test_run.id]) == 1

    @pytest.mark.integration
    def test_list_runs_extended_with_header(self,
                                            test_client,
                                            test_run,
                                            OIDC_credentials):
        response = test_client.get("/weskit/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert len([x for x in response.json if x['run_id'] == test_run.id]) == 1
        assert response.json[0].keys() == \
               {"request", "run_id", "run_status", "start_time", "user_id"}

    @pytest.mark.integration
    def test_get_run_status(self,
                            test_client,
                            test_run,
                            OIDC_credentials):
        run_id = test_run.id
        response = test_client.get(f"/ga4gh/wes/v1/runs/{run_id}/status",
                                   headers=OIDC_credentials.headerToken)
        start_time = time.time()
        while response.status_code == 409:   # workflow still running
            assert is_within_timeout(start_time, 20), "Timeout requesting status"
            time.sleep(1)
            response = test_client.get(f"/ga4gh/wes/v1/runs/{run_id}/status",
                                       headers=OIDC_credentials.headerToken)

        assert response.status_code == 200
        assert response.json == {
            "run_id": run_id,
            "state": "COMPLETE"
        }

    @pytest.mark.integration
    def test_get_nonexisting_run_status(self,
                                        test_client,
                                        OIDC_credentials):
        response = test_client.get("/weskit/v1/runs/nonExistingRun/status",
                                   headers=OIDC_credentials.headerToken)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_run(self,
                     test_client,
                     OIDC_credentials):
        response = test_client.get("/weskit/v1/runs/nonExistingRun",
                                   headers=OIDC_credentials.headerToken)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_run_stderr_with_header(self,
                                        test_client,
                                        test_run,
                                        OIDC_credentials):
        run_id = test_run.id
        response = test_client.get(f"/weskit/v1/runs/{run_id}/stderr",
                                   headers=OIDC_credentials.headerToken)
        start_time = time.time()
        while response.status_code == 409:   # workflow still running
            assert is_within_timeout(start_time, 20), "Timeout requesting stderr"
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
        run_id = test_run.id
        response = test_client.get(f"/weskit/v1/runs/{run_id}/stdout",
                                   headers=OIDC_credentials.headerToken)
        start_time = time.time()
        while response.status_code == 409:    # workflow still running
            assert is_within_timeout(start_time, 20), "Timeout requesting stdout"
            time.sleep(1)
            response = test_client.get(f"/weskit/v1/runs/{run_id}/stdout",
                                       headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert isinstance(response.json, dict)
        assert "content" in response.json


class TestManagerRaiseError:

    @pytest.mark.integration
    def test_update_run_fails_with_missing_celery_id(self, long_run):
        long_run.celery_task_id = None
        with pytest.raises(RuntimeError):
            current_app.manager.update_run(long_run)

    @pytest.mark.integration
    def test_fails_reexecute_active_run(self, long_run):
        with pytest.raises(RuntimeError):
            current_app.manager.execute(long_run)

    @pytest.mark.integration
    def test_fails_prepare_execution(self, long_run):
        with pytest.raises(RuntimeError):
            current_app.manager.prepare_execution(long_run)
