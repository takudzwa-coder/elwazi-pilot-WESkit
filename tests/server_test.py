import json
import time
import yaml
import os
import requests

# Global Variable
access_token=None
session_token=None
headerToken=None

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
    
def test_get_access_token(test_app):
    global access_token
    global session_token
    global headerToken
    print("____")
    print(os.environ["testing_only_tokenendpoint"])
    payload = {
        "grant_type": "password",
        "username": "test",
        "password": "test",
        "client_id": "OTP",
        "client_secret": "7670fd00-9318-44c2-bda3-1a1d2743492d"
    }
    r2=requests.post(url=os.environ["testing_only_tokenendpoint"],data=payload).json()
    access_token=r2.get('access_token',"None2")
    session_token=r2.get('session_state',"None2")
    print(access_token)
    headerToken={'Authorization': 'Bearer %s'%access_token}
    assert True 

def test_get_service_info(test_app):
    response = test_app.get("/ga4gh/wes/v1/service-info")
    print(headerToken)
    assert response.status_code == 200


def test_LoginRestriction(test_app):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=headerToken)
    assert response.status_code == 401
    

def test_run_workflow(test_app, celery_worker):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=headerToken)
    run_id = response.json["run_id"]
    running = True
    while running:
        time.sleep(1)
        status = test_app.get(
            "/ga4gh/wes/v1/runs/{}/status".format(run_id)
        )
        if (status.json == "COMPLETE"):
            running = False
    assert response.status_code == 200

def test_get_runs(test_app, celery_worker):
    response = test_app.get("/ga4gh/wes/v1/runs", headers=headerToken)
    assert response.status_code == 200

# def test_logout(test_app):
    # loginData=dict()
    # response=test_app.post("/logout",data=loginData)
    # assert response.status == '200 OK'
    
# def test_Logout_Successfull(test_app):
    # snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    # data = get_workflow_data(
        # snakefile=snakefile,
        # config="tests/wf1/config.yaml")
    # response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    # assert response.status_code == 401
