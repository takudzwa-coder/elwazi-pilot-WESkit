from celery import Celery
import sys


def make_celery(app_name=__name__):
    celery = Celery(
        app=app_name,
        broker="redis://localhost:6379",
        backend="redis://localhost:6379")
    return(celery)


print("start celery client", file=sys.stderr)
celery = make_celery()
