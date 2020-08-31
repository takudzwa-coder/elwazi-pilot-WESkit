def init_celery(celery, app):
    print(app.config)
    celery_config = dict()
    celery_config["broker_url"] = "redis://{}:{}".format(
        app.config["message_queue"]["host"],
        str(app.config["message_queue"]["port"]))

    celery_config["result_backend"] = "redis://{}:{}".format(
        app.config["message_queue"]["host"],
        str(app.config["message_queue"]["port"]))

    celery.conf.update(celery_config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
