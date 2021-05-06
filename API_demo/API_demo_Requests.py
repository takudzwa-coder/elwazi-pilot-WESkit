#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import requests
import os
import yaml
import json

weskit_host = "https://localhost:5000"
keycloak_host = "https://localhost:8443/auth/realms/WESkit/protocol/openid-connect/token"

Credentials = dict(
    username="test",
    password="test",
    client_id="OTP",
    client_secret="7670fd00-9318-44c2-bda3-1a1d2743492d"
)

current_file = os.path.dirname(os.path.abspath(__file__))
# Set path for self signed certificate

cert = os.path.normpath(os.path.join(current_file, '../uWSGI_Server/certs/weskit.pem'))


def get_workflow_data():
    with open(os.path.normpath(os.path.join(current_file, '../tests/wf1/config.yaml'))) as file:
        workflow_params = yaml.load(file, Loader=yaml.FullLoader)
    snakefile = "file:tests/wf1/Snakefile"
    data = {
        "workflow_params": workflow_params,
        "workflow_type": "snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": snakefile
    }
    return data


def get_access_token_from_keycloak(hostname, credentials):
    credentials["grant_type"] = "password"
    print("These credentials will be submitted to keycloak:")
    print(yaml.dump(credentials))
    print(hostname)
    response = requests.post(url=hostname, data=credentials, verify=cert).json()
    print("Keycloak response:")
    print(yaml.dump(response))
    return response


def tryApiEndpoints(loginType, cookie=None, header=None):
    print("****************************************")
    print("%s - GET-Requst to '/ga4gh/wes/v1/service-info'" % (loginType))

    response1 = requests.get("%s/ga4gh/wes/v1/service-info" % (weskit_host), verify=cert)

    print("Status Code:", response1.status_code)
    print("Response:", response1.json())
    print("****************************************\n\n")

    response2 = requests.post("%s/ga4gh/wes/v1/runs" % (weskit_host),
                              json=get_workflow_data(),
                              headers=header,
                              cookies=cookie,
                              verify=cert)
    print(response2.status_code)
    print(response2.json())

    print("****************************************")
    print("%s - GET-Requst to '/ga4gh/wes/v1/runs/'" % (loginType))

    response3 = requests.get("%s/ga4gh/wes/v1/runs" % (weskit_host),
                             headers=header,
                             cookies=cookie,
                             verify=cert)

    print("Status Code:", response3.status_code)
    print("Response:")
    print(yaml.dump(response3.json()))
    print("****************************************\n\n")

    print("****************************************")
    print(
        "%s - GET-Requst to '/ga4gh/wes/v1/runs/%s/status'" %
        (loginType, response2.json()['run_id']))

    response4 = requests.get(
        "%s/ga4gh/wes/v1/runs/%s/status" % (weskit_host, response2.json()['run_id']),
        headers=header,
        cookies=cookie,
        verify=cert)

    print("Status Code:", response4.status_code)
    print("Response:", response4.json())
    print("****************************************\n\n")


token = get_access_token_from_keycloak(hostname=keycloak_host, credentials=Credentials)

print("****************************************")
print("*  Test API access token in header     *")

header = dict(Authorization="Bearer " + token["access_token"])
print(header)
tryApiEndpoints('with access token in Header ', header=header)
print("________________________________________________________________________________")
