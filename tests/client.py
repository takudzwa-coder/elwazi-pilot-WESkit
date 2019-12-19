import requests
import os
import json
import yaml
import subprocess

baseurl = "http://127.0.0.1:8080/ga4gh/wes/v1"


workflow_params = json.dumps({"text":"blablablubb"})

parts =  [("workflow_params", workflow_params),
    ("workflow_type", "Snakemake"),
    ("workflow_type_version", "5.8.2"),
    ("workflow_url", os.getcwd() + "/wf1/Snakefile")]

sendwf = requests.post("{}/runs".format(baseurl), data=parts)
sendwf.json()

requests.get("{}/runs".format(baseurl))
requests.get("{}/runs/{}".format(baseurl, sendwf.json()["run_id"])).json()

sendwf2 = requests.post("{}/runs".format(baseurl), data=parts)
sendwf2.json()

requests.post("{}/runs/{}/cancel".format(baseurl, sendwf2.json()["run_id"]))
requests.get("{}/runs".format(baseurl)).json()