from flask import current_app
from ga4gh.wes.utils import create_run_id

# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return query_result, 200


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    run = current_app.database.get_run(run_id)
    if run is None:
        return {"msg": "Key %s not found" % run_id,
                "status_code": 0
        }, 404
    else:
        # TODO perform steps to delete run: set status on canceled and stop running processes
        #database.delete_run(run_id)
        run = current_app.snakemake.cancel(run)
        return {"run_id": run.run_id}, 200


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return {k: query_result[k] for k in ["run_id", "run_status"]}, 200


# get:/service-info
def GetServiceInfo(*args, **kwargs):
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
    response = current_app.database.list_run_ids_and_states()
    return response, 200


# post:/runs
def RunWorkflow(*args, **kwargs):
       run = current_app.database.create_new_run(create_run_id(), request=kwargs)
       run = current_app.snakemake.execute(run, current_app.database)
       return {k: run[k] for k in ["run_id"]}, 200