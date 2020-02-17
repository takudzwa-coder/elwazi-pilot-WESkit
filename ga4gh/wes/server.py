from ga4gh.wes.RunStatus import RunStatus
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
    run = current_app.database.create_new_run(create_run_id(), kwargs)

    # create run environment
    run = _create_environment(run)

    # execute run
    run = _execute_run(run)
    return run.pretty(), 200


def create_run_id():
    print("_create_run_id")
    # create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length = 8
    run_id = "".join(choice(charset) for __ in range(length))
    return run_id


def _execute_run(run):
    print("_execute_run")
    new_run = run.copy()
    tmp_dir = "tmp/" + current_app.database.get_run_id(new_run)
    command = [
        "snakemake",
        "--snakefile", new_run["request"]["workflow_url"],
        "--directory", tmp_dir,
        "all"]
    new_run.run_status = RunStatus.Running
    new_run.start_time = current_app.database.get_current_time()
    new_run["run_log"]["cmd"] = " ".join(command)
    current_app.database.update_run(new_run)
    with open(tmp_dir + "/stdout.txt", "w") as fout:
        with open(tmp_dir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    new_run.run_status = RunStatus.Complete
    new_run.end_time = current_app.database.get_current_time()
    current_app.database.update_run(new_run)
    return new_run


def _create_environment(run):
    tmp_dir = "tmp/"
    print("_create_environment")
    run_dir = os.path.abspath(os.path.join(tmp_dir, run.run_id))
    os.makedirs(run_dir)
    with open(run_dir + "/config.yaml", "w") as ff:
        yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
    new_run = run.copy()
    new_run.environment_path = run_dir
    current_app.database.update_run(new_run)
    return new_run
