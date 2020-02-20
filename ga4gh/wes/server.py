from ga4gh.wes.RunStatus import RunStatus
import os, subprocess, json, yaml
from flask import current_app
from random import choice
import pprint


# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    print("GetRunLog")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return query_result, 200


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    print("CancelRun")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        return {"msg": "Key %s not found" % run_id,
                "status_code": 0
                }, 404
    else:
        current_app.database.delete_run(run_id)
        return run_id, 200


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    print("GetRunStatus")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return {k: query_result[k] for k in ["run_id", "run_status"]}, 200



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
    response = current_app.database.list_run_ids_and_states()
    return response, 200


# post:/runs
def RunWorkflow(*args, **kwargs):
    print("RunWorkflow")
    run = current_app.database.create_new_run(create_run_id(), kwargs)

    # create run environment
    run = create_environment(run)

    # execute run
    run = execute_run(run)
    return pprint.pprint(run), 200                                                                                      # should return (only?) the run_id -> s. documentation


def create_run_id():
    print("_create_run_id")
    # create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length = 8
    run_id = "".join(choice(charset) for __ in range(length))
    return run_id


def execute_run(run):
    print("_execute_run")
    new_run = run.copy()
    tmp_dir = "tmp/" + new_run["run_id"]
    command = [
        "snakemake",
        "--snakefile", new_run["request"]["workflow_url"],
        "--directory", tmp_dir,
        "all"]
    new_run["run_status"] = RunStatus.Running.encode()
    new_run["start_time"] = current_app.database.get_current_time()
    new_run["run_log"]["cmd"] = " ".join(command)
    current_app.database.update_run(new_run)
    with open(tmp_dir + "/stdout.txt", "w") as fout:
        with open(tmp_dir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    new_run["run_status"] = RunStatus.Complete.encode()
    new_run["end_time"] = current_app.database.get_current_time()
    current_app.database.update_run(new_run)
    return new_run


def create_environment(run):
    tmp_dir = "tmp/"
    print("_create_environment")
    run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
    os.makedirs(run_dir)
    with open(run_dir + "/config.yaml", "w") as ff:
        yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
    new_run = run.copy()
    new_run["environment_path"] = run_dir                                                                               # environment_path = workflow_url ?
    current_app.database.update_run(new_run)
    return new_run
