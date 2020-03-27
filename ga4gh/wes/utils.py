import uuid
from datetime import datetime
from flask import current_app


def create_run_id():
    current_app.info_logger.info("create_run_id")
    run_id = str(uuid.uuid4())
    while current_app.database.get_run(run_id) == run_id:
        run_id = str(uuid.uuid4())
    return run_id


def get_current_time():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
