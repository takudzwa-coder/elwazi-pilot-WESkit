import requests
import os
import yaml
import json
from time import sleep

s = requests.session()
s.verify=False

weskit_host = "https://localhost:5000"
keycloak_host = "https://localhost:8443/auth/realms/WESkit/protocol/openid-connect/token"

Credentials = dict(
    username="test",
    password="test",
    client_id="OTP",
    client_secret="7670fd00-9318-44c2-bda3-1a1d2743492d"
)

loginresponse = s.post("%s/login" % (weskit_host), json=Credentials)
print("Status Code:", loginresponse.status_code)
print("Response:", loginresponse.json())
current_file = os.path.dirname(os.path.abspath(__file__))


def get_workflow_data():
    with open(os.path.normpath(os.path.join(current_file, '../tests/wf1/config.yaml'))) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))
    snakefile = "file:tests/wf1/Snakefile"
    data = {
        "workflow_params": workflow_params,
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": snakefile
    }
    return data



def tryApiEndpoints():
    print("****************************************")
    print("Requesting 'service-info'")

    response1 = s.get("%s/ga4gh/wes/v1/service-info" % (weskit_host))

    print("Status Code:", response1.status_code)
    print("Response:", response1.text)




    print("****************************************\n\n")
    print("Submitting Workflow to 'runs'")
    response2 = s.post("%s/ga4gh/wes/v1/runs" % (weskit_host),data=get_workflow_data())
    print(response2.status_code)
    print(response2.text)

    print("_______________________________________")
    print("Now WESkit is Gone")
    print("I submitted to '%s/ga4gh/wes/v1/runs'\nData:" % weskit_host)
    print(yaml.dump(get_workflow_data()))
    print("_______________________________________")


    print("****************************************")
    print("Request Running Workflows from runs'")
    response3 = s.get("%s/ga4gh/wes/v1/runs" % (weskit_host))
    print("Status Code:", response3.status_code)
    print("Response:")
    print(response3.text)




    print("****************************************")
    print("Request Status from '/runs/%s/status'" % ( response2.json()['run_id']))

    response4 = s.get("%s/ga4gh/wes/v1/runs/%s/status" % (
                            weskit_host,
                            response2.json()['run_id']))

    print("Status Code:", response4.status_code)
    print("Response:", response4.text)



    print("****************************************")
    print("Requesting again 'service-info'")

    response5 = s.get("%s/ga4gh/wes/v1/service-info" % (weskit_host))

    print("Status Code:", response5.status_code)
    print("Response:", response5.text)



print("****************************************")
print("*  Test API access token in Cookie     *")

tryApiEndpoints()
print("________________________________________________________________________________")
