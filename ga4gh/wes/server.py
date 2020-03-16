import ga4gh.wes.server_implementation as impl
import ga4gh.wes.workflow_executor_service as wes
from flask import current_app


# get:/runs/{run_id}
<<<<<<< Updated upstream
def GetRunLog(run_id, *args, **kwargs):
    return impl.GetRun(current_app, run_id, *args, **kwargs)
=======
def GetRunLog(run_id, log_config, *args, **kwargs):
    log.log_info(log_config, "GetRun")
    query_result = current_app.database.get_run(run_id)
    if query_result is None:
        log.log_error(log_config, "Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return query_result, 200
>>>>>>> Stashed changes


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    return impl.CancelRun(current_app, run_id, *args, **kwargs)


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    return impl.GetRunStatus(current_app, run_id, *args, **kwargs)


# get:/service-info
def GetServiceInfo(*args, **kwargs):
    return impl.GetServiceInfo(current_app, *args, **kwargs)


# get:/runs
def ListRuns(*args, **kwargs):
    return impl.ListRuns(current_app, *args, **kwargs)


# post:/runs
<<<<<<< Updated upstream
def RunWorkflow(*args, **kwargs):
    return impl.RunWorkflow(current_app, *args, **kwargs)


def create_run_id():
    return impl.create_run_id()


def execute_run(run):
    return wes.execute_run(current_app, run)


def create_environment(run):
    return wes.create_environment(current_app, run)
=======
def RunWorkflow(log_config, *args, **kwargs):
    log.log_info(log_config, "RunWorkflow")
    run = current_app.database.create_new_run(create_run_id(), request=kwargs)
    run = current_app.snakemake.execute(run, current_app.database, log_config)
    return {k: run[k] for k in ["run_id"]}, 200
>>>>>>> Stashed changes
