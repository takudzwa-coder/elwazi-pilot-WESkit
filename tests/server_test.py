import json
import time
import yaml
import os
import requests

# Global Variable
access_token=None
session_token=None
headerToken=None
runID=None

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
    session_token={"X-Csrf-Token":r2.get('session_state',"None2")}
    print(session_token)
    headerToken={'Authorization': 'Bearer %s'%access_token}
    assert True 

def test_get_service_info(test_app):
    response = test_app.get("/ga4gh/wes/v1/service-info")
    print(headerToken)
    assert response.status_code == 200

################################################
#         Test Closed Endpoints                #
################################################


def test_list_runs_wo_login(test_app):
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401
    


def test_submit_workflow_wo_login(test_app, celery_worker):
    global runID
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    assert response.status_code == 401


#################################################
#           Header Token (OTP Mode)             #
#################################################

def test_run_workflow_header(test_app, celery_worker):
    global runID
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=headerToken)
    run_id = response.json["run_id"]
    runID = response.json["run_id"]
    running = True
    while running:
        time.sleep(1)
        status = test_app.get(
            "/ga4gh/wes/v1/runs/{}/status".format(run_id),
            headers=headerToken
        )
        if (status.json == "COMPLETE"):
            running = False
    assert response.status_code == 200


def test_get_runs_header(test_app, celery_worker):
    response = test_app.get("/ga4gh/wes/v1/runs", headers=headerToken)
    assert len([x for x in response.json if x['run_id']== runID])==1
    assert response.status_code == 200
    
#################################################
#     Cookie Login (WEB Frondend Mode)          #
#            only Session Token                 #
#################################################

def test_run_workflow_CSRF_only(test_app, celery_worker):
    global runID
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=session_token)
    assert response.status_code == 401
    assert response.data == b'{"msg":"Missing JWT in cookies or headers (Missing cookie \\"access_token_cookie\\"; Missing Authorization Header)"}\n'


def test_get_runs_CSRF_only(test_app, celery_worker):
    response = test_app.get("/ga4gh/wes/v1/runs", headers=session_token)
    assert response.status_code == 401
    assert response.data == b'{"msg":"Missing JWT in cookies or headers (Missing cookie \\"access_token_cookie\\"; Missing Authorization Header)"}\n'


#################################################
#     Cookie Login (WEB Frondend Mode)          #
#            only Cookie                 #
#################################################

def test_run_workflow_cookie_only(test_app, celery_worker):
    global runID
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    test_app.set_cookie('localhost', 'access_token_cookie', access_token)
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data)
    print("FOOOO")
    print(response.data)
    assert response.status_code == 401
    assert response.data == b'{"msg":"Cookie Login detected: X-CSRF-TOKEN is not submitted via Header!"}\n'


def test_get_runs_cookie_only(test_app, celery_worker):
    response = test_app.get("/ga4gh/wes/v1/runs")
    assert response.status_code == 401
    assert response.data == b'{"msg":"Cookie Login detected: X-CSRF-TOKEN is not submitted via Header!"}\n'



#################################################
#     Cookie Login (WEB Frondend Mode)          #
#             Correct Webauth                   #
#################################################

def test_run_workflow_cookie(test_app, celery_worker):
    global runID
    snakefile = os.path.join(os.getcwd(), "tests/wf1/Snakefile")
    test_app.set_cookie('localhost', 'access_token_cookie', access_token)
    data = get_workflow_data(
        snakefile=snakefile,
        config="tests/wf1/config.yaml")
    response = test_app.post("/ga4gh/wes/v1/runs", data=data, headers=session_token)
    run_id = response.json["run_id"]
    runID = response.json["run_id"]
    print(response.json)
    running = True
    while running:
        time.sleep(1)
        status = test_app.get(
            "/ga4gh/wes/v1/runs/{}/status".format(run_id),
            headers=session_token
        )
        print(status.data)
        print(status.json)
        if (status.json == "COMPLETE"):
            running = False
    assert response.status_code == 200


def test_get_runs_cookie(test_app, celery_worker):
    response = test_app.get("/ga4gh/wes/v1/runs", headers=session_token)
    assert len([x for x in response.json if x['run_id']== runID])==1
    assert response.status_code == 200


def test_sleep_4_redis(test_app, celery_worker):
    time.sleep(5)
    assert(True) 