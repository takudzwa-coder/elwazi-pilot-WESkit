import logging
import os
import pytest
import yaml
from weskit.classes.Database import Database
from weskit.classes.ServiceInfo import ServiceInfo
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from testcontainers.compose import DockerCompose
from logging.config import dictConfig
from weskit.classes.RunStatus import RunStatus




def get_redis_url(redis_container):
    url = "redis://{}:{}".format(
        redis_container.get_container_host_ip(),
        redis_container.get_exposed_port(6379)
    )
    return url


@pytest.fixture(scope="session")
def test_app(database_container, redis_container,keycloak_container):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    os.environ["kc_backend"]="http://%s:%s/auth/realms/WESkit" % (
        keycloak_container.get_service_host("keycloak",8080),
        keycloak_container.get_service_port("keycloak",8080),
    )

    # import here because env vars need to be set before
    from weskit import create_app

    os.environ["WESKIT_CONFIG"] = "tests/config.yaml"

    app = create_app()
    
    os.environ["testing_only_tokenendpoint"]=app.OIDC_Login.oidc_config["token_endpoint"]
    app.testing = True
    with app.test_client() as testing_client:
        ctx = app.app_context()
        ctx.push()
        yield testing_client

@pytest.fixture(scope="session")
def keycloak_container():

    kc_container = DockerCompose("./kc_login","docker-compose.yaml")
    kc_container.start()
    return kc_container
    
@pytest.fixture(scope="session")
def test_config():
    # This uses a dedicated test configuration YAML.
    with open("tests/config.yaml", "r") as ff:
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
def database_connection(database_container):
    from weskit import create_database

    database = create_database()

    yield database
    database._db_runs().drop()

@pytest.fixture(scope="session")
def redis_container():
    redis_container = RedisContainer("redis:6.0.1-alpine")
    redis_container.start()
    return redis_container


@pytest.fixture(scope="session")
def celery_config(redis_container):
    return {
        "broker_url": get_redis_url(redis_container),
        "result_backend": get_redis_url(redis_container)
    }


#@pytest.fixture(scope="session")
#def celery_worker_pool():
#    return 'prefork'


@pytest.fixture(scope="session")
def service_info(test_config, swagger, database_connection):
    yield ServiceInfo(
        test_config["static_service_info"],
        swagger,
        database_connection
    )


@pytest.fixture(scope="session")
def swagger(database_connection):
    with open("weskit/api/workflow_execution_service_1.0.0.yaml",
              "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger


@pytest.fixture(scope="session")
def manager(database_connection, redis_container, test_config):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    from weskit.classes.Manager import Manager
    manager = Manager(config=test_config, datadir="tmp/")
    yield manager
