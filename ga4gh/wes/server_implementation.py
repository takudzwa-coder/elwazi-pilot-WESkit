import ga4gh.wes.workflow_executor_service as wes
import ga4gh.wes.logging_configs as log
import ga4gh.wes.service_info as info
from random import choice
import yaml, os


# get:/runs/{run_id}
def GetRun(current_app, run_id, *args, **kwargs):
    log.log_info("GetRun")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        log.log_error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return query_result, 200


# post:/runs/{run_id}/cancel
def CancelRun(current_app, run_id, *args, **kwargs):
    log.log_info("CancelRun")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        log.log_error("Key %s not found" % run_id)
        return {"msg": "Key %s not found" % run_id,
                "status_code": 0
                }, 404
    else:
        current_app.database.delete_run(run_id)
        log.log_info("Run %s deleted from database" % run_id)
        return {"run_id": run_id}, 200
    # ToDo: Cancel a running Snakemake process


# get:/runs/{run_id}/status
def GetRunStatus(current_app, run_id, *args, **kwargs):
    log.log_info("GetRunStatus")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        log.log_error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return {k: query_result[k] for k in ["run_id", "run_status"]}, 200


# get:/service-info
def GetServiceInfo(current_app, *args, **kwargs):
    config = current_app.config
    print(config)
    log.log_info("GetServiceInfo")
    path = os.path.abspath(os.path.join("2191217_workflow_execution_service.swagger.yaml"))
    with open(path) as ff:
        api_swagger = yaml.load(ff, Loader=yaml.FullLoader)
    service_info_yaml = info.load_yaml()
    response = {
        "workflow_type_versions": service_info_yaml["workflow_type_versions"],
        "supported_wes_versions": [api_swagger["info"]["version"]],
        "supported_filesystem_protocols": [service_info_yaml["supported_filesystem_protocols"]],
        "workflow_engine_versions": service_info_yaml["workflow_engine_versions"],
        "default_workflow_engine_parameters": [service_info_yaml["default_workflow_engine_parameters"]],
        "system_state_counts": service_info_yaml["system_state_counts"],
        "auth_instructions_url": service_info_yaml["auth_instructions_url"],
        "contact_info_url": service_info_yaml["contact_info_url"],
        "tags": service_info_yaml["tags"]
    }
    return response, 200


# get:/runs
def ListRuns(current_app, *args, **kwargs):
    log.log_info("ListRuns")
    response = current_app.database.list_run_ids_and_states()
    return response, 200


# post:/runs
def RunWorkflow(current_app, *args, **kwargs):
    log_msg = log.log_info("RunWorkflow")
    run = current_app.database.create_new_run(create_run_id(), kwargs)
    new_run = run.copy()
    new_run["run_log"] = log_msg
    current_app.database.update_run(new_run)
    
    # create run environment
    run = wes.create_environment(current_app, run)

    # execute run
    run = wes.execute_run(current_app, run)
    return {k: run[k] for k in ["run_id"]}, 200


def create_run_id():
    log.log_info("_create_run_id")
    # create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length = 8
    run_id = "".join(choice(charset) for __ in range(length))
    return run_id
