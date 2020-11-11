from celery import Celery

celery_app = Celery(
    app="wesnake",
    broker="redis://result_broker:6379",
    backend="redis://result_broker:6379")


if __name__ == '__main__':
    celery_app.start()
