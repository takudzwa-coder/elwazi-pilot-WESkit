import weskit
import os
from weskit.tasks.CommandTask import run_command

celery_app = weskit.create_celery(
    os.environ["BROKER_URL"],
    os.environ["RESULT_BACKEND"]
    )

celery_app.task(run_command)
