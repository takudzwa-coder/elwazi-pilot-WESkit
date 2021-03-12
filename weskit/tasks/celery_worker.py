from weskit.tasks.celery import celery_app
import os


celery_config = dict()
celery_config["broker_url"] = os.environ["BROKER_URL"]
celery_config["result_backend"] = os.environ["RESULT_BACKEND"]
celery_config["task_track_started"] = True
celery_app.conf.update(celery_config)
