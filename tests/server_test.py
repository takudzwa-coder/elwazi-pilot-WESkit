import json
import time
import yaml
import os


def get_workflow_data(workflow_file, config):
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": workflow_file
    }
    return data


def test_get_service_info(test_client):
    response = test_client.get("/ga4gh/wes/v1/service-info")
    assert response.status_code == 200


def test_login_restriction(test_client):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        workflow_file=snakefile,
        config="tests/wf1/config.yaml")
    response = test_client.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401


def test_login(test_client):
    login_data = {'password': 'test', 'username': 'test'}
    response = test_client.post("/login", data=login_data)
    assert response.status == '302 FOUND'


def test_missing_fields_run_request(test_client, celery_session_worker):
    complete_data = {
        "workflow_params": {},
        "workflow_type": "snakemake",
        "workflow_type_version": "5",
        "workflow_url": "https://some.git.repo/path/to/it.git"
    }
    for key in complete_data.keys():
        reduced_data = complete_data.copy()
        del reduced_data[key]
        response = test_client.post("/ga4gh/wes/v1/runs", data=reduced_data)
        assert response.status_code == 400
        assert response.json["msg"] == \
               "Malformed request: [{'%s': ['required field']}]" % key


# WARNING: This test fails with 401 unauthorized, if run isolated.
#          Run it together with the other server_test.py tests!
def test_run_snakemake(test_client, celery_session_worker):
    snakefile = "file:tests/wf1/Snakefile"
    data = get_workflow_data(
        workflow_file=snakefile,
        config="tests/wf1/config.yaml")
    response = test_client.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 200
    run_id = response.json["run_id"]
    success = False
    start_time = time.time()
    while not success:
        time.sleep(1)
        assert (start_time - time.time()) <= 30, "Test timed out"
        status = test_client.get(
            "/ga4gh/wes/v1/runs/{}/status".format(run_id)
        )
        print("Waiting ... (status=%s)" % status.json)
        if status.json in ["UNKNOWN", "EXECUTOR_ERROR", "SYSTEM_ERROR",
                           "CANCELED", "CANCELING"]:
            assert False, "Failing run status '{}'".format(status.json)
        elif status.json == "COMPLETE":
            success = True


def test_get_runs(test_client):
    response = test_client.get("/ga4gh/wes/v1/runs")
    assert response.status_code == 200


def test_logout(test_client):
    login_data = dict()
    response = test_client.post("/logout", data=login_data)
    assert response.status == '200 OK'


def test_logout_successfull(test_client):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        workflow_file=snakefile,
        config="tests/wf1/config.yaml")
    response = test_client.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401
