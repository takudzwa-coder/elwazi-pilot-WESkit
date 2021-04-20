import json
import time

import yaml
import os
import requests
import pytest
from flask import current_app

@pytest.fixture(name="runStorage", scope="class")
def runid_fixture():
    """
    This fixture returns a class that stores the run ID as variable within a Test Class.
    This makes it possible to exchange variables between tests of a class without using
    global variables

    accessible via "runStorage.runid" if runStorage is declared in the call of the testfunction
    """

    class RunID:
        def __init__(self):
            self.runid = ""

    return RunID()


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

            r2 = requests.post(url=current_app.OIDC_Login.oidc_config["token_endpoint"], data=payload).json()
            self.access_token = r2.get('access_token', "None2")
            self.session_token = {"X-Csrf-Token": r2.get('session_state', "None2")}
            self.headerToken = {'Authorization': 'Bearer %s' % self.access_token}

    return LoginClass()


def get_workflow_data(snakefile, config):
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": "file:tests/wf1/Snakefile"
    }
    return data


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoint that should be accessible without
    login are accessible.
    """
    @pytest.mark.integration
    def test_get_service_info(self, test_client):
        response = test_client.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200


class TestWithoutLogin:
    """
    The TestWithoutLogin class ensures that all secured endpoints are not accessible without
    credentials.
    """
    @pytest.mark.integration
    def test_list_runs_wo_login(self, test_client, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_client.post("/ga4gh/wes/v1/runs", data=data)
        assert response.status_code == 401

    @pytest.mark.integration
    def test_submit_workflow_wo_login(self, test_client, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_client.post("/ga4gh/wes/v1/runs", data=data)
        assert response.status_code == 401


class TestWithHeaderToken:
    """
    The TestWithHeaderToken class ensures that some protected endpoints are accessible by
    submitting an access token in the request header in the format
    "'Authorization': 'Bearer xxxxxxxxxxxxxxxx-xxxx-xxxxxxxxxx"
    """

    @pytest.mark.integration
    def test_accept_run_workflow_header(
            self,
            test_client,
            runStorage,
            OIDC_credentials,
            celery_worker):

        data = get_workflow_data(
            snakefile="tests/wf1/Snakefile",
            config="tests/wf1/config.yaml")

        response = test_client.post(
            "/ga4gh/wes/v1/runs", data=data, headers=OIDC_credentials.headerToken)

        run_id = response.json["run_id"]

        runStorage.runid = response.json["run_id"]
        success = False
        start_time = time.time()
        while not success:

            time.sleep(1)
            status = test_client.get(
                "/ga4gh/wes/v1/runs/{}/status".format(run_id),
                headers=OIDC_credentials.headerToken
            )
            assert (time.time() - start_time) <= 30, "Test timed out"

            print("Waiting ... (status=%s)" % status.json)
            if status.json in ["UNKNOWN", "EXECUTOR_ERROR", "SYSTEM_ERROR",
                               "CANCELED", "CANCELING"]:
                assert False, "Failing run status '{}'".format(status.json)

            if status.json == "COMPLETE":
                success = True

        assert response.status_code == 200

    @pytest.mark.integration
    def test_accept_get_runs_header(self, test_client, runStorage, OIDC_credentials, celery_worker):
        response = test_client.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.headerToken)
        assert len([x for x in response.json if x['run_id'] == runStorage.runid]) == 1
        assert response.status_code == 200
