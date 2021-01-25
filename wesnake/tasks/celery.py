from celery import Celery
import os

celery_app = Celery(
    app="weskit",
    broker=os.environ.get("BROKER_URL"),
    backend=os.environ.get("RESULT_BACKEND")
)


if __name__ == '__main__':
    celery_app.start()
