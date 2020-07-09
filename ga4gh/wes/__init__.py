from celery import Celery


def make_celery(app_name=__name__):
    celery = Celery(
        app="celery_app",
        broker="redis://result_broker:6379",
        backend="redis://result_broker:6379",
        include=["ga4gh.wes.tasks"])
    return(celery)


celery = make_celery()
