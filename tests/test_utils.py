import uuid
from weskit.classes.Run import Run


def get_mock_run(workflow_url, workflow_type, tags=None):
    data = {
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
    }
    if tags is not None:
        data["request"]["tags"] = tags
    run = Run(data)
    return run
