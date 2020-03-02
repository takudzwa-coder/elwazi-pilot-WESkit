from flask import current_app
from ga4gh.wes.utils import create_run_id

# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    return current_app.snakemake.get_run(run_id, current_app.database)


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    return current_app.snakemake.post_run_cancel(run_id, current_app.database)


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    return current_app.snakemake.get_run_status(current_app, run_id, current_app.database)


# get:/service-info
def GetServiceInfo(*args, **kwargs):
    return current_app.snakemake.get_service_info()


# get:/runs
def ListRuns(*args, **kwargs):
    return current_app.snakemake.get_runs(current_app.database)


# post:/runs
def RunWorkflow(*args, **kwargs):
       run = current_app.database.create_new_run(create_run_id(), request=kwargs)
       return current_app.snakemake.post_run(run, current_app.database)