import ga4gh.wes.server_implementation as impl
import ga4gh.wes.workflow_executor_service as wes
from flask import current_app


# get:/runs/{run_id}
def GetRunLog(run_id, *args, **kwargs):
    return impl.GetRun(current_app, run_id, *args, **kwargs)


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
def RunWorkflow(*args, **kwargs):
    return impl.RunWorkflow(current_app, *args, **kwargs)


def create_run_id():
    return impl.create_run_id()


def execute_run(run):
    return wes.execute_run(current_app, run)


def create_environment(run):
    return wes.create_environment(current_app, run)
