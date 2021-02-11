import uuid
from weskit.classes.Run import Run


def get_mock_run(workflow_url, workflow_type, publish_dir=""):
    run = Run({
        "run_id": str(uuid.uuid4()),
        "run_status": "UNKNOWN",
        "request_time": None,
        "request": {
            "workflow_url": workflow_url,
            "workflow_type": workflow_type,
            "workflow_params": '{"text":"hello_world"}',
            "publish_dir": publish_dir
        },
        "execution_path": [],
        "run_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    })
    return run
