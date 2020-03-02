#import ga4gh.wes.server_implementation as impl
#import ga4gh.wes.workflow_executor_service as wes
from flask import current_app
from ga4gh.wes.utils import create_run_id

database = current_app.database
snakemake = current_app.snakemake

# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    return snakemake.get_run(current_app, run_id)


# post:/runs/{run_id}/cancel
def CancelRun(run_id, *args, **kwargs):
    return snakemake.post_run_cancel(current_app, run_id)


# get:/runs/{run_id}/status
def GetRunStatus(run_id, *args, **kwargs):
    return snakemake.get_run_status(current_app, run_id)


# get:/service-info
def GetServiceInfo(*args, **kwargs):
    return snakemake.get_service_info()


# get:/runs
def ListRuns(*args, **kwargs):
    return snakemake.get_runs()


# post:/runs
def RunWorkflow(*args, **kwargs):
    run = database.create_new_run(create_run_id(), request=kwargs)
    return snakemake.post_run(run)