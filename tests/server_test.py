import json
import time
import yaml
import os

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

def test_get_service_info(test_app):
    response = test_app.get("/ga4gh/wes/v1/service-info")
    assert response.status_code == 200
    
    
def test_LoginRestriction(test_app):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401
    
def test_login (test_app):
    loginData={'password':'test','username':'test'}
    response=test_app.post("/login",data=loginData)
    assert response.status == '302 FOUND'

def test_run_workflow(test_app, celery_worker):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
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
    response = test_app.get("/ga4gh/wes/v1/runs")
    #print
    assert response.status_code == 200

def test_logout(test_app):
    loginData=dict()
    response=test_app.post("/logout",data=loginData)
    assert response.status == '200 OK'
    
def test_Logout_Successfull(test_app):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401
