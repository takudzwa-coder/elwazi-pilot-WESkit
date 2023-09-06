# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime
from urllib.parse import urlparse

import pytest
import requests
import time
from flask import current_app as flask_current_app
from validators.url import url as validate_url

from test_utils import \
    assert_within_timeout, is_within_timeout, assert_stage_is_not_failed, get_workflow_data
from weskit import WESApp
from weskit.api.Helper import Helper
from weskit.api.RunStatus import RunStatus
from weskit.classes.ProcessingStage import ProcessingStage
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
    Engine parameters are used to also test their serialization/deserialization.
    """
    current_app = WESApp.from_current_app(flask_current_app)
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf1/Snakefile",
        config="tests/wf1/config.yaml",
        engine_params={
            "max-memory": "150m",
            "max-runtime": "00:01:00",
            "accounting-name": "projectX",
            "job-name": "testjob",
            "group": "testgroup",
            "queue": "testqueue"
        })
    run = manager.create_and_insert_run(validated_request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run = manager.prepare_execution(run)
    run = manager.execute(run)
    run = manager.database.update_run(run)
    success = False
    start_time = time.time()
    while not success:
        assert_within_timeout(start_time)
        stage = run.processing_stage
        if stage != ProcessingStage.FINISHED_EXECUTION:
            assert_stage_is_not_failed(stage)
            print("Waiting ... (stage=%s)" % stage.name)
            time.sleep(1)
            run = current_app.manager.update_run(run)
            continue
        success = True
    assert (run.run_dir(manager.weskit_context) / "hello_world.txt").is_file()
    assert "hello_world.txt" in to_filename(run.outputs["filesystem"])
    yield run


@pytest.fixture(scope="module")
def incomplete_run(test_client,
                   celery_session_worker):
    current_app = WESApp.from_current_app(flask_current_app)
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf1/Snakefile",
        config="tests/wf2/config.yaml")
    run = manager.create_and_insert_run(validated_request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run.request["workflow_params"]["duration"] = 1
    run = manager.prepare_execution(run)
    manager.database.update_run(run)
    return run


@pytest.fixture(scope="function")
def long_run(test_client,
             celery_session_worker):
    current_app = WESApp.from_current_app(flask_current_app)
    manager = current_app.manager
    request = get_workflow_data(
        snakefile="file:tests/wf2/Snakefile",
        config="tests/wf2/config.yaml")
    run = manager.create_and_insert_run(validated_request=request,
                                        user_id="6bd12400-6fc4-402c-9180-83bddbc30526")
    run.request["workflow_params"]["duration"] = 10
    run = manager.prepare_execution(run)
    run = manager.execute(run)
    run = manager.database.update_run(run)
    start_time = time.time()
    stage = ProcessingStage.PREPARED_EXECUTION
    while stage != ProcessingStage.SUBMITTED_EXECUTION:
        assert_within_timeout(start_time)
        stage = run.processing_stage
        assert_stage_is_not_failed(stage)
        print("Waiting ... (stage=%s)" % stage.name)
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
            current_app = WESApp.from_current_app(flask_current_app)
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
        """
        Test that the response conforms to the specification according to the Swagger file.
        """
        response = test_client.get("/ga4gh/wes/v1/service-info")
        assert response.status_code == 200, response.json
        assert set(response.json.keys()) == {
            "workflow_type_versions", "supported_wes_versions",
            "supported_filesystem_protocols", "workflow_engine_versions",
            "default_workflow_engine_parameters", "system_state_counts",
            "auth_instructions_url", "contact_info_url", "tags"
        }
        assert response.json["workflow_type_versions"] == {
            "NFL": {
              "workflow_type_version": [
                "23.04.1"
              ]
            },
            "SMK": {
              "workflow_type_version": [
                "7.30.2"
              ]
            }
          }
        assert response.json["supported_wes_versions"] == ["1.0.0"]
        assert response.json["supported_filesystem_protocols"] == ["file", "S3"]
        assert response.json["workflow_engine_versions"] == {
            "NFL": "23.04.1",
            "SMK": "7.30.2"
          }

        def as_dict(params: list):
            """Used to make get to dictionaries that are comparable by ==."""
            return {p["name"]: p for p in params}

        assert as_dict(response.json["default_workflow_engine_parameters"]) == as_dict([
              {"name": "SMK|7.30.2|engine-environment",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "SMK|7.30.2|max-memory",
               "default_value": "100m",
               "type": "Optional[str validFor Python.memory_units.Memory.from_str($)]"},
              {"name": "SMK|7.30.2|max-runtime",
               "default_value": "05:00",
               "type": "Optional[str validFor Python.tempora.parse_timedelta($)]"},
              {"name": "SMK|7.30.2|accounting-name",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "SMK|7.30.2|job-name",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "SMK|7.30.2|group",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "SMK|7.30.2|queue",
               "default_value": None,
               "type": "Optional[str]"},

              {"name": "NFL|23.04.1|accounting-name",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "NFL|23.04.1|job-name",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "NFL|23.04.1|group",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "NFL|23.04.1|queue",
               "default_value": None,
               "type": "Optional[str]"},
              {"name": "NFL|23.04.1|trace",
               "default_value": "true",
               "type": "bool"},
              {"name": "NFL|23.04.1|timeline",
               "default_value": "true",
               "type": "bool"},
              {"name": "NFL|23.04.1|graph",
               "default_value": "true",
               "type": "bool"},
              {"name": "NFL|23.04.1|report",
               "default_value": "true",
               "type": "bool"}
          ])
        assert response.json["auth_instructions_url"] == "https://somewhere.org"
        assert response.json["contact_info_url"] == "mailto:your@email.de"
        assert response.json["tags"] == {
              "tag1": "value1",
              "tag2": "value2"
          }
        assert set(response.json["system_state_counts"].keys()) == {
            'CANCELED', 'CANCELING', 'COMPLETE', 'EXECUTOR_ERROR', 'INITIALIZING',
            'PAUSED', 'QUEUED', 'RUNNING', 'SYSTEM_ERROR'
        }
        for v in response.json["system_state_counts"].values():
            assert type(v) is int

        for status in RunStatus:
            assert status.name in response.json["system_state_counts"].keys()


class TestWithoutLogin:
    """
    The TestWithoutLogin class ensures that all secured endpoints are not accessible without
    credentials.
    """
    @pytest.mark.integration
    def test_get_run_stage(self, test_client):
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
    def test_submit_workflow_wo_login(self, test_client):
        data = get_workflow_data(
            snakefile="file:tests/wf1/Snakefile",
            config="tests/wf1/config.yaml")
        response = test_client.post("/ga4gh/wes/v1/runs",
                                    data=data,
                                    headers={"Content-Type": "multipart/form-data"})
        assert response.status_code == 401


class TestWithHeaderToken:
    """
    The TestWithHeaderToken class ensures that some protected endpoints are accessible by
    submitting an access token in the request header in the format
    "'Authorization': 'Bearer xxxxxxxxxxxxxxxx-xxxx-xxxxxxxxxx"
    """

    @pytest.mark.integration
    def test_submit_workflow_upload(self,
                                    test_client,
                                    OIDC_credentials):

        data = {}
        data["workflow_params"] = '{"text": "hello world"}'
        data["workflow_url"] = "Snakefile"
        data["workflow_type"] = "SMK"
        data["workflow_type_version"] = "7.30.2"
        data["workflow_attachment"] = (open("tests/wf1/Snakefile", "rb"), "Snakefile")
        data["workflow_engine_parameters"] = "{}"

        response = test_client.post(
            "/ga4gh/wes/v1/runs",
            data=data,
            content_type="multipart/form-data",
            headers=OIDC_credentials.headerToken)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_fails_requests(self,
                            test_client,
                            OIDC_credentials):

        test_client.post("/ga4gh/wes/v1/runs",
                         headers=OIDC_credentials.headerToken)
        fake_run_id = "fds-fsd,"

        # Retrieve the status of non-existing run
        status_response = test_client.get(f"/ga4gh/wes/v1/runs/{fake_run_id}/status",
                                          headers=OIDC_credentials.headerToken)
        assert status_response.status_code == 500

        # Retrieve the RunLog of non-existing run
        log_response = test_client.get(f"/ga4gh/wes/v1/runs/{fake_run_id}",
                                       headers=OIDC_credentials.headerToken)
        assert log_response.status_code == 500

        # Cancel nonexisting run
        cancel_response_fail = test_client.post(f"/ga4gh/wes/v1/runs/{fake_run_id}/cancel",
                                                headers=OIDC_credentials.headerToken)
        assert cancel_response_fail.status_code == 500

    @pytest.mark.integration
    def test_fails_submit_data(self,
                               test_client,
                               OIDC_credentials):

        # Submit empty data
        data = {}
        response = test_client.post(
            "/ga4gh/wes/v1/runs",
            data=data,
            content_type="multipart/form-data",
            headers=OIDC_credentials.headerToken)
        assert response.status_code == 400

        # Submit wrong data structure
        data["workflow_url"] = {"bla": {"Snakefile"}}
        response_corrup = test_client.post(
            "/ga4gh/wes/v1/runs",
            data=data,
            content_type="multipart/form-data",
            headers=OIDC_credentials.headerToken)
        assert response_corrup.status_code == 400

    @pytest.mark.integration
    def test_get_run(self,
                     test_client,
                     OIDC_credentials):
        # Submit a new workflow. The test should be end-to-end, i.e. also the processing of the
        # string-formatted parameters in the upload into a dict structure in the RunLog is tested.
        data = {}
        data["workflow_params"] = '{"text": "hello world"}'
        data["workflow_url"] = "file:tests/wf1/Snakefile"
        data["workflow_type"] = "SMK"
        data["workflow_type_version"] = "7.30.2"
        data["workflow_engine_parameters"] = """
        {
            "max-memory": "150m",
            "max-runtime": "00:01:00",
            "accounting-name": "projectX",
            "job-name": "testjob",
            "group": "testgroup",
            "queue": "testqueue"
        }
        """
        submission_response = test_client.post(
            "/ga4gh/wes/v1/runs",
            data=data,
            content_type="multipart/form-data",
            headers=OIDC_credentials.headerToken)
        assert submission_response.status_code == 200

        run_id = submission_response.json["run_id"]

        # Status request.
        status_response = test_client.get(f"/ga4gh/wes/v1/runs/{run_id}/status",
                                          headers=OIDC_credentials.headerToken)
        status_start_time = time.time()
        while status_response.json["state"] != "COMPLETE":
            # workflow still running
            assert is_within_timeout(status_start_time, 20), "Timeout requesting status"
            time.sleep(1)
            status_response = test_client.get(f"/ga4gh/wes/v1/runs/{run_id}/status",
                                              headers=OIDC_credentials.headerToken)

        # Now, retrieve the RunLog.
        log_response = test_client.get(f"/ga4gh/wes/v1/runs/{run_id}",
                                       headers=OIDC_credentials.headerToken)

        assert log_response.status_code == 200, log_response.json
        assert log_response.json["run_id"] == run_id

        assert log_response.json["request"] == {
            # Note that the workflow_params and workflow_engine_parameters are uploaded as string
            # form-data, but are expected to be JSON in the RunLog response (i.e. not represented
            # as string).
            "workflow_params": {
                "text": "hello world"
            },
            "workflow_engine_parameters": {
                "max-memory": "150m",
                "max-runtime": "00:01:00",
                "accounting-name": "projectX",
                "job-name": "testjob",
                "group": "testgroup",
                "queue": "testqueue"
            },
            "workflow_type": "SMK",
            "workflow_type_version": "7.30.2",
            # tags should be a string of JSON text. JSON "null" is mapped to None in Python and
            # valid JSON. This is what we return, if no tags were provided at submission.
            "tags": None,
            "workflow_url": "file:tests/wf1/Snakefile"
        }

        assert log_response.json["state"] == "COMPLETE"

        assert log_response.json["run_log"].keys() == {
            "name", "cmd", "exit_code", "start_time", "end_time", "stdout", "stderr"
        }

        # It is not clear from the documentation or discussion what the "workflow name" should be
        # We use the path to the workflow file (workflow_url) for now.
        assert log_response.json["run_log"]["name"] == log_response.json["request"]["workflow_url"]
        assert log_response.json["run_log"]["cmd"] == [
            'snakemake',
            '--snakefile',
            '../../../tests/wf1/Snakefile',
            '--cores',
            '1',
            '--configfile',
            f"{run_id}.yaml"
        ]

        assert log_response.json["run_log"]["exit_code"] == 0
        start_time = log_response.json["run_log"]["start_time"]
        assert datetime.fromisoformat(start_time)

        end_time = log_response.json["run_log"]["end_time"]
        assert datetime.fromisoformat(end_time)

        stdout = log_response.json["run_log"]["stdout"]
        stdout_parsed = urlparse(stdout)
        assert stdout_parsed.path == f".weskit/{start_time}/stdout"

        stderr = log_response.json["run_log"]["stderr"]
        stderr_parsed = urlparse(stderr)
        assert stderr_parsed.path == f".weskit/{start_time}/stderr"

        # At the time, the structure of the "outputs" field is not defined, except that it should
        # be a dictionary. See specification 1.0.0 and mentioning in this discussion:
        # https://github.com/ga4gh/workflow-execution-service-schemas/issues/176
        assert "hello_world.txt" in log_response.json["outputs"]["filesystem"]
        assert f"{run_id}.yaml" in log_response.json["outputs"]["filesystem"]
        # Not checking the log files, though.

        # Test that S3 outputs are valid URLs
        for output_url in log_response.json["outputs"]["S3"]:
            assert validate_url(output_url)

        # Files in the S3 output should be the same, and in the same order as in the filesystem.
        for idx in range(0, len(log_response.json["outputs"]["filesystem"])):
            path = urlparse(log_response.json["outputs"]["filesystem"][idx]).path
            s3 = urlparse(log_response.json["outputs"]["S3"][idx]).path
            assert path in s3

        assert log_response.json["task_logs"] == []
        # TODO Implement for issue #95 and #266.
        # "task_logs": [
        #   {
        #     "name": "string",
        #     "cmd": [
        #       "string"
        #     ],
        #     "start_time": "string",
        #     "end_time": "string",
        #     "stdout": "string",
        #     "stderr": "string",
        #     "exit_code": 0
        #   }
        # ]

    @pytest.mark.integration
    def test_get_runs(self,
                      test_client,
                      test_run,
                      OIDC_credentials):
        response = test_client.get("/ga4gh/wes/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert response.json["next_page_token"] == ""   # For now, everything on one page.
        runs = [x for x in response.json["runs"] if x['run_id'] == str(test_run.id)]
        assert len(runs) == 1
        assert runs[0] == {
            "run_id": str(test_run.id),
            "state": "COMPLETE"
        }

    @pytest.mark.integration
    def test_list_runs_extended(self,
                                test_client,
                                test_run,
                                OIDC_credentials):
        response = test_client.get("/weskit/v1/runs", headers=OIDC_credentials.headerToken)
        assert response.status_code == 200, response.json
        assert len([x for x in response.json if x['run_id'] == str(test_run.id)]) == 1
        assert response.json[0].keys() == \
               {"request", "run_id", "run_stage", "start_time", "user_id"}

    @pytest.mark.integration
    def test_get_run_stage(self,
                           test_client,
                           test_run,
                           OIDC_credentials):
        run_id = str(test_run.id)
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
    def test_get_nonexisting_run_stage(self,
                                       test_client,
                                       OIDC_credentials):
        response = test_client.get("/weskit/v1/runs/nonExistingRun/status",
                                   headers=OIDC_credentials.headerToken)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_nonexisting_run(self,
                                 test_client,
                                 OIDC_credentials):
        response = test_client.get("/weskit/v1/runs/nonExistingRun",
                                   headers=OIDC_credentials.headerToken)
        assert response.status_code == 404


class TestExceptionError:

    def raise_error(self, client, wes_route, OIDC_credentials):
        with pytest.raises(AttributeError):
            client.get(wes_route, headers=OIDC_credentials.headerToken)

    @pytest.mark.integration
    def test_raise_error(self,
                         test_client,
                         test_run,
                         OIDC_credentials):

        current_app = WESApp.from_current_app(flask_current_app)

        run_id = test_run.id

        # Setting the manager to None really is just a quick way to create the exceptions.
        # We use reflection, rather than making the manager field Optional in WESApp.
        current_app._manager = None     # no type

        # fails to get run log
        self.raise_error(test_client, f"/ga4gh/wes/v1/runs/{run_id}", OIDC_credentials)

        # fails to get run status
        self.raise_error(test_client, f"/ga4gh/wes/v1/runs/{run_id}/status", OIDC_credentials)

        # fails to get serviceInfo
        self.raise_error(test_client, "/ga4gh/wes/v1/service-info", OIDC_credentials)

        # fails to list runs
        self.raise_error(test_client, "/ga4gh/wes/v1/runs", OIDC_credentials)

        # fails to list runs extended
        self.raise_error(test_client, "/weskit/v1/runs", OIDC_credentials)


class TestOICDValidationError:

    @pytest.mark.integration
    def test_raise_OICD_validataion_error(self,
                                          test_client,
                                          test_run,
                                          OIDC_credentials):

        current_app = WESApp.from_current_app(flask_current_app)

        current_app.config["userinfo_validation_value"] = "XXX"
        response = test_client.post("/ga4gh/wes/v1/runs",
                                    headers=OIDC_credentials.headerToken)
        response.status_code == 401

        current_app.oidc_login.client_id = " "
        current_app.oidc_login.client_secret = " "
        response = test_client.post("/ga4gh/wes/v1/runs",
                                    headers=OIDC_credentials.headerToken)
        response.status_code == 401
