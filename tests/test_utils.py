import uuid
from weskit.classes.Run import Run
import time

def get_mock_run(workflow_url, workflow_type):
    run = Run({
        "run_id": str(uuid.uuid4()),
        "run_status": "INITIALIZING",
        "request_time": None,
        "request": {
            "workflow_url": workflow_url,
            "workflow_type": workflow_type,
            "workflow_params": '{"text":"hello_world"}',
        },
        "execution_path": [],
        "run_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    })
    return run


def get_run_success(status, start_time):
    assert (time.time() - start_time) <= 30, "Test timed out"

    print("Waiting ... (status=%s)" % status)
    if status in ["UNKNOWN", "EXECUTOR_ERROR", "SYSTEM_ERROR",
                       "CANCELED", "CANCELING"]:
        assert False, "Failing run status '{}'".format(status)

    if status == "COMPLETE":
        return True

    return False
