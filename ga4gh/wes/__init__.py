from celery import Celery


def make_celery(app_name=__name__):
    celery = Celery(
        app=app_name,
        broker="redis://localhost:6379",
        backend="redis://localhost:6379",
        include=["ga4gh.wes.tasks"])
    return(celery)


celery = make_celery()
