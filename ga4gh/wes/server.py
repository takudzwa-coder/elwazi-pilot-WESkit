import ga4gh.wes.service_info_validation as service_info_validate
import cerberus
from ga4gh.wes.utils import create_run_id
from flask import current_app


# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    current_app.logger.info("GetRun")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        current_app.logger.error("Could not find %s" % run_id)
        # ToDo: Maybe print this error to the console as well?
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return query_result, 200


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    current_app.logger.info("CancelRun")
    run = current_app.database.get_run(run_id)
    if run is None:
        current_app.logger.error("Could not find %s" % run_id)
        # ToDo: Maybe print this error to the console as well?
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        # TODO perform steps to delete run: set status on canceled and stop running processes
        run = current_app.snakemake.cancel(run)
        current_app.logger.info("Run %s is canceled" % run_id)
        return {"run_id": run.run_id}, 200


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    current_app.logger.info("GetRunStatus")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        current_app.logger.error("Could not find %s" % run_id)
        # ToDo: Maybe print this error to the console as well?
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return {k: query_result[k] for k in ["run_id", "run_status"]}, 200


# get:/service-info
def GetServiceInfo(service_info, service_info_validation, *args, **kwargs):
    current_app.logger.info("GetServiceInfo")
    validator = service_info_validate.validate_service_info(service_info, service_info_validation)
    if validator is False:
        raise cerberus.schema.SchemaError
    response = {
        "workflow_type_versions": current_app.service_info.get_workflow_type_versions(),
        "supported_wes_versions": current_app.service_info.get_supported_wes_versions(),
        "supported_filesystem_protocols": current_app.service_info.get_supported_filesystem_protocols,
        "workflow_engine_versions": current_app.service_info.get_workflow_engine_versions(),
        "default_workflow_engine_parameters": current_app.service_info.get_default_workflow_engine_parameters(),
        "system_state_counts": current_app.service_info.get_system_state_counts(),
        "auth_instructions_url": current_app.service_info.get_auth_instructions_url(),
        "contact_info_url": current_app.service_info.get_contact_info_url(),
        "tags": current_app.service_info.get_tags()
    }
    return response, 200


# get:/runs
def ListRuns(*args, **kwargs):
    current_app.logger.info("ListRuns")
    response = current_app.database.list_run_ids_and_states()
    return response, 200


# post:/runs
def RunWorkflow(*args, **kwargs):
    current_app.logger.info("RunWorkflow")
    run = current_app.database.create_new_run(create_run_id(), request=kwargs)
    run = current_app.snakemake.execute(run, current_app.database)
    return {k: run[k] for k in ["run_id"]}, 200
