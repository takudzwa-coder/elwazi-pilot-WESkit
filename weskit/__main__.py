from weskit import create_database, create_celery
from weskit import create_app


def main():
    app = create_app(create_celery(),
                     create_database())
    app.run(host="0.0.0.0", port=5000)
