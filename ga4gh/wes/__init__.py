from celery import Celery


def make_celery(app_name=__name__):
    celery = Celery(app="tmp_name", broker="redis://redis:6379", backend="redis://redis:6379")
    return(celery)

celery = make_celery()