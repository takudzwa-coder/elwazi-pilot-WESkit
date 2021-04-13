import os
import pytest
import yaml

from weskit.classes.ServiceInfo import ServiceInfo
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from weskit import create_app, Manager, WorkflowEngineFactory
from weskit import create_database


def get_redis_url(redis_container):
    url = "redis://{}:{}".format(
        redis_container.get_container_host_ip(),
        redis_container.get_exposed_port(6379)
    )
    return url


@pytest.fixture(scope="session")
def test_client(celery_session_app,
                celery_session_worker,
                test_database,
                redis_container):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    os.environ["WESKIT_CONFIG"] = "tests/weskit.yaml"
    os.environ["WESKIT_DATA"] = "test-data/"

    app = create_app(celery=celery_session_app,
                     database=test_database)
    app.testing = True
    with app.test_client() as testing_client:
        with app.app_context():
            # This sets `current_app` for accessing the Flask app in the tests.
            yield testing_client


@pytest.fixture(scope="session")
def test_config():
    # This uses a dedicated test configuration YAML.
    with open("tests/weskit.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="session")
def database_container():
    MONGODB_CONTAINER = "mongo:4.2.3"

    db_container = MongoDbContainer(MONGODB_CONTAINER)
    db_container.start()
    os.environ["WESKIT_DATABASE_URL"] = db_container.get_connection_url()

    yield db_container


@pytest.fixture(scope="session")
def test_database(database_container):
    database = create_database(database_container.get_connection_url())
    yield database
    database._db_runs().drop()


@pytest.fixture(scope="session")
def redis_container():
    redis_container = RedisContainer("redis:6.0.1-alpine")
    redis_container.start()
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    return redis_container


@pytest.fixture(scope="session")
def celery_config(redis_container):
    return {
        "broker_url": get_redis_url(redis_container),
        "result_backend": get_redis_url(redis_container),
        "task_track_started": True
    }


@pytest.fixture(scope="session")
def service_info(test_config, swagger, test_database):
    yield ServiceInfo(
        test_config["static_service_info"],
        swagger,
        test_database
    )


@pytest.fixture(scope="session")
def swagger():
    with open("weskit/api/workflow_execution_service_1.0.0.yaml",
              "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger


@pytest.fixture(scope="session")
def manager(celery_session_app, redis_container, test_config, test_database):
    workflows_base_dir = os.path.abspath(os.getcwd())
    os.environ["WESKIT_WORKFLOWS"] = workflows_base_dir
    test_dir = "test-data/"
    if not os.path.isdir(test_dir):
        os.mkdir(test_dir)
    return Manager(celery_app=celery_session_app,
                   database=test_database,
                   workflow_engines=WorkflowEngineFactory.
                   workflow_engine_index(
                       test_config
                       ["static_service_info"]
                       ["default_workflow_engine_parameters"]),
                   workflows_base_dir=workflows_base_dir,
                   data_dir=test_dir,
                   use_custom_workdir=False)
