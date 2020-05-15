from celery import Celery


def make_celery(app_name=__name__):
    celery = Celery(
        app="celery_app",
        broker="redis://redis:6379",
        backend="redis://redis:6379",
        include=["ga4gh.wes.tasks"])
    return(celery)

celery = make_celery()