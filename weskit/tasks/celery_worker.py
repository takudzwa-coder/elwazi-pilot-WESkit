import weskit
import os
from weskit.tasks.WorkflowTask import run_workflow

celery_app = weskit.create_celery(
    os.environ["BROKER_URL"],
    os.environ["RESULT_BACKEND"]
    )

celery_app.task(run_workflow)
