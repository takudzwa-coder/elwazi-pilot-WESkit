import json
import time
import yaml
import os
import requests
import pytest


@pytest.fixture(name="runStorage", scope="class")
def runid_fixture():
    """
    This fixture returns a class that stores the run ID as variable within a Test Class.
    This makes it possible to exchange variables between tests of a class without using global variables

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
            print("____")
            print(os.environ["testing_only_tokenendpoint"])
            payload = {
                "grant_type": "password",
                "username": "test",
                "password": "test",
                "client_id": "OTP",
                "client_secret": "7670fd00-9318-44c2-bda3-1a1d2743492d"
            }
            r2 = requests.post(url=os.environ["testing_only_tokenendpoint"], data=payload).json()
            self.access_token = r2.get('access_token', "None2")
            self.session_token = {"X-Csrf-Token": r2.get('session_state', "None2")}
            self.headerToken = {'Authorization': 'Bearer %s' % self.access_token}

    return LoginClass()


def get_workflow_data(snakefile, config):
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "Snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": snakefile
    }
    return data


class TestOpenEndpoint:
    """
    The TestOpenEndpoint class ensures that all endpoint that should be accessible without login are accessible.
    """

    def test_get_service_info(self, test_app):
        response = test_app.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200


class TestWithoutLogin:
    """
    The TestWithoutLogin class ensures that all secured endpoints are not accessible without credentials.
    """

    def test_list_runs_wo_login(self, test_app):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data)
        assert response.status_code == 401

    def test_submit_workflow_wo_login(self, test_app, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data)
        assert response.status_code == 401


class TestWithHeaderToken:
    """
    The TestWithHeaderToken class ensures that some protected endpoints are accessible by submitting an access token in
    the request header in the format "'Authorization': 'Bearer xxxxxxxxxxxxxxxx-xxxx-xxxxxxxxxx"
    """

    def test_run_workflow_header(self, test_app, runStorage, OIDC_credentials, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=OIDC_credentials.headerToken)
        run_id = response.json["run_id"]
        runStorage.runid = response.json["run_id"]
        running = True
        while running:
            time.sleep(1)
            status = test_app.get(
                "/ga4gh/wes/v1/runs/{}/status".format(run_id),
                headers=OIDC_credentials.headerToken
            )
            if status.json == "COMPLETE":
                running = False
        assert response.status_code == 200

    def test_get_runs_header(self, test_app, runStorage, OIDC_credentials, celery_worker):
        response = test_app.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.headerToken)
        assert len([x for x in response.json if x['run_id'] == runStorage.runid]) == 1
        assert response.status_code == 200


class TestCSRFTokenOnly:
    """
    The TestCSRFTokenOnly class ensures that it is impossible to access the endpoint by only submitting the session
    token without an access token as Cookie.
    """

    def test_run_workflow_CSRF_only(self, test_app, OIDC_credentials, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=OIDC_credentials.session_token)
        assert response.status_code == 401
        assert response.data == b'{"msg":"Missing JWT in cookies or headers (Missing cookie' \
                                b' \\"access_token_cookie\\"; Missing Authorization Header)"}\n'

    def test_get_runs_CSRF_only(self, test_app, OIDC_credentials, celery_worker):
        response = test_app.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.session_token)
        assert response.status_code == 401
        assert response.data == b'{"msg":"Missing JWT in cookies or headers (Missing cookie' \
                                b' \\"access_token_cookie\\"; Missing Authorization Header)"}\n'



class TestMissingCSRFToken:
    """
    The TestMissingCSRFToken class ensures that it is impossible to access the endpoints by only submitting the access
    cookie with out the session token in the header.
    """

    def test_run_workflow_cookie_only(self, test_app, OIDC_credentials, celery_worker):
        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        test_app.set_cookie('localhost', 'access_token_cookie', OIDC_credentials.access_token)
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data)
        print("FOOOO")
        print(response.data)
        assert response.status_code == 401
        assert response.data == b'{"msg":"Cookie Login detected: X-CSRF-TOKEN is not submitted via Header!"}\n'

    def test_get_runs_cookie_only(self, test_app, celery_worker):
        response = test_app.get("/ga4gh/wes/v1/runs")
        assert response.status_code == 401
        assert response.data == b'{"msg":"Cookie Login detected: X-CSRF-TOKEN is not submitted via Header!"}\n'


class TestWithCookie:
    """
    This TestWithCookie tests the correct functionality of the secured endpoint by using cookies with session token
    """

    def test_run_workflow_cookie(self, test_app, runStorage, OIDC_credentials, celery_worker):

        snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
        test_app.set_cookie('localhost', 'access_token_cookie', OIDC_credentials.access_token)
        data = get_workflow_data(
            snakefile=snakefile,
            config="tests/wf1/config.yaml")
        response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=OIDC_credentials.session_token)
        run_id = response.json["run_id"]
        runStorage.runid = response.json["run_id"]
        print(response.json)
        running = True
        while running:
            time.sleep(1)
            status = test_app.get(
                "/ga4gh/wes/v1/runs/{}/status".format(run_id),
                headers=OIDC_credentials.session_token
            )
            print(status.data)
            print(status.json)
            if status.json == "COMPLETE":
                running = False
        assert response.status_code == 200

    def test_get_runs_cookie(self, test_app, runStorage, OIDC_credentials, celery_worker):
        response = test_app.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.session_token)
        assert len([x for x in response.json if x['run_id'] == runStorage.runid]) == 1
        assert response.status_code == 200


def test_sleep_4_redis(test_app, celery_worker):
    """
    This function adds just some delay to allow celery finishing its task before the redis container is stopped
    """
    time.sleep(5)
    assert True
