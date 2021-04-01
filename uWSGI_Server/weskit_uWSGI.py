from weskit import create_app, create_celery, create_database

app = create_app(create_celery(),
                 create_database())
