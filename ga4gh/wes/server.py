from ga4gh.wes.Database import Database
import os, subprocess, json, yaml

from datetime import datetime
from flask import current_app
from connexion import NoContent
from connexion import request
from random import choice


# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    print("GetRunLog")
    response = current_app.database.information_run(run_id)
    return response, 200


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    print("CancelRun")
    try:
        current_app.database.delete_run(run_id)
        return NoContent, 200
    except KeyError:
        print("Key not found")
        return NoContent, 404


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    print("GetRunStatus")
    response = current_app.database.information_run(run_id)
    return response, 200


# get:/service-info
def GetServiceInfo(*args, **kwargs):
    config = current_app.config
    print(config)
    print("GetServiceInfo")
    response = {
        "supported_wes_versions": "1.0.0",
        "supported_filesystem_protocols": "file",
        "workflow_engine_versions": "snakemake 5.8.2",
        "default_workflow_engine_parameters": [],
        "system_state_counts": {},
        "auth_instructions_url": "",
        "contact_info_url": "sven.twardziok@charite.de",
        "tags": {}
    }
    return response, 200


# get:/runs
def ListRuns(*args, **kwargs):
    print("ListRuns")
    response = current_app.database.list_runs()
    return response, 200


# post:/runs
def RunWorkflow(*args, **kwargs):
    print("RunWorkflow")
    
    # create run object
    run_id = create_run_id(*args, **kwargs)

    # store run object
    current_app.database.store_run_id(run_id)
    current_app.database.store_run_status(run_id)
    current_app.database.store_run_request_time(run_id)

    # create run environment
    _create_environment(run_id)

    # execute run
    _execute_run(run_id)

    response = current_app.database.information_run(run_id)
    return response, 200


def create_run_id(*args, **kwargs):
    print("_create_run_id")
    # create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length = 8
    run_id = "".join(choice(charset) for __ in range(length))
    return run_id


def _execute_run(run):
    print("_execute_run")
    tmp_dir = "tmp/" + current_app.database.get_run_id(run)
    command = [
        "snakemake",
        "--snakefile", run["request"]["workflow_url"],
        "--directory", tmp_dir,
        "all"]
    current_app.database.store_run_status(run)
    current_app.database.store_run_start_time(run)
    run["run_log"]["cmd"] = " ".join(command)
    with open(tmp_dir + "/stdout.txt", "w") as fout:
        with open(tmp_dir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    current_app.database.store_run_end_time()
    current_app.database.store_run_status(run)

    return current_app.database.information_run(run)


def _create_environment(run):
    tmp_dir = "tmp/"
    print("_create_environment")
    run_dir = os.path.abspath(os.path.join(tmp_dir, current_app.database.get_run_id(run)))
    os.makedirs(run_dir)
    with open(run_dir + "/config.yaml", "w") as ff:
        yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
    return True
