import os, subprocess, yaml, json

from datetime import datetime
from connexion import request
from flask import current_app
from connexion import NoContent
from connexion import request
from random import choice

runs = {}

# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    print("GetRunLog")
    response = _load_run(run_id)
    return response, 200
   
# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    print("CancelRun")
    try:
        del runs[run_id]
        return NoContent, 200
    except KeyError:
        print("Key not found")
        return NoContent, 404

# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    print("GetRunStatus")
    run = _load_run(run_id)
    response = {
        "run_id":run_id,
        "state":run["state"]
    }
    return response, 200

# get:/service-info
def GetServiceInfo(*args, **kwargs):
    config=current_app.config
    print(config)
    print("GetServiceInfo")
    response = {
        "supported_wes_versions":"1.0.0",
        "supported_filesystem_protocols": "file",
        "workflow_engine_versions":"snakemake 5.8.2",
        "default_workflow_engine_parameters":[],
        "system_state_counts":{},
        "auth_instructions_url":"",
        "contact_info_url":"sven.twardziok@charite.de",
        "tags":{}
    }
    return response, 200

# get:/runs
def ListRuns(*args, **kwargs):
    print("ListRuns")
    response = []
    for run in runs:
        response.append({
        "run_id":runs[run]["run_id"],
        "state":runs[run]["state"]})
    return response, 200

# post:/runs
def RunWorkflow(*args, **kwargs):
    print("RunWorkflow")
    
    #create run object  
    run = _create_run(*args, **kwargs)
    
    # create run environment
    _create_environment(run)

    #store run object
    _store_run(run)

    # execute run
    _execute_run(run)

    response = {"run_id": run["run_id"]}
    return response, 200

def _create_run(*args, **kwargs):
    print("_create_run")
    #create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length=8
    run_id = "".join(choice(charset) for __ in range(length)) 
    #create run dict  
    run = dict()
    run["run_id"] = run_id
    run["request"] = kwargs
    run["state"] = "UNKNOWN"
    run["run_log"] = dict()
    run["task_logs"] = list()
    run["outputs"] = dict()
    return run

def _store_run(run):
    runs[run["run_id"]] = run
    return True

def _load_run(run_id):
    return  runs[run_id]

def _execute_run(run):
    print("_execute_run")
    tmp_dir = "tmp/"+ run["run_id"]
    command = [
        "snakemake",
        "--snakefile", run["request"]["workflow_url"],
        "--directory", tmp_dir,
        "all"]
    run["state"] = "RUNNING"
    run["run_log"]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    run["run_log"]["cmd"] = " ".join(command)
    with open(tmp_dir + "/stdout.txt","w") as fout:
        with open(tmp_dir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    run["run_log"]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    run["state"] = "COMPLETE"

    return run

def _create_environment(run):
    tmp_dir = "tmp/"
    print("_create_environment")
    run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
    os.makedirs(run_dir)
    with open(run_dir + "/config.yaml", "w") as ff:
        yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
    return True
    