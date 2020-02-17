from ga4gh.wes.server import *
from ga4gh.wes.app import *

run_id = create_run_id()

with app.app_context():
    RunWorkflow()
    GetServiceInfo()
    ListRuns()
    GetRunStatus(run_id)
    GetRunLog(run_id)
    CancelRun(run_id)
