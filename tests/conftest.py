import pytest, yaml, os, logging, sys
from ga4gh.wes.Database import Database
from ga4gh.wes.Snakemake import Snakemake
from ga4gh.wes.ServiceInfo import ServiceInfo
from ga4gh.wes.wesnake import create_app
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from logging.config import dictConfig


@pytest.fixture(scope="function")
def test_app(test_config, validation, log_config,
             logger, database_connection):
    app = create_app(test_config, validation, log_config, logger, database_connection)
    app.app.testing = True
    with app.app.test_client() as testing_client:
        ctx = app.app.app_context()
        ctx.push()
        yield testing_client


@pytest.fixture(scope="function")
def test_config():
    # This uses a dedicated test configuration YAML.
    with open("tests/config.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="function")
def validation():
    # This uses the global validation YAML because YAML file structures should be identical in test and production.
    with open(os.path.join("config", "validation.yaml"), "r") as ff:
        validation = yaml.load(ff, Loader=yaml.FullLoader)
    yield validation


@pytest.fixture(scope="function")
def database_connection():
    MONGODB_URI = "MONGODB_URI"
    MONGODB_CONTAINER = "mongo:4.2.3"
    WESNAKE_TEST_DB = "WESnake_Test"

    if MONGODB_URI in os.environ.keys() and os.environ[MONGODB_URI].upper() == "DOCKER":
        container = MongoDbContainer(MONGODB_CONTAINER)
        container.start()
        database = Database(MongoClient(container.get_connection_url()), WESNAKE_TEST_DB)
    elif MONGODB_URI in os.environ.keys() and os.environ[MONGODB_URI] != "":
        connection_url = os.environ[MONGODB_URI]
        database = Database(MongoClient(connection_url), WESNAKE_TEST_DB)
    else:
        database = Database(MongoClient(), WESNAKE_TEST_DB)

    yield database
    database._db_runs().drop()

@pytest.fixture(scope='function')
def redis_container():
    print("redis_container")
    redis_container = RedisContainer("redis:6.0.1-alpine")
    redis_container.start()
    return redis_container

@pytest.fixture(scope='function')
def celery_config(redis_container):
    print("celery_config")
    #time.sleep(10)
    #client = container.get_client()
    tmp = {
        'broker_url': "redis://" + redis_container.get_container_host_ip() + ":" + redis_container.get_exposed_port(6379),
        'result_backend': "redis://" + redis_container.get_container_host_ip() + ":" + redis_container.get_exposed_port(6379)
    }
    #time.sleep(10)
    print(tmp)
    return tmp

@pytest.fixture(scope="function")
def snakemake_executor():
    executor = Snakemake()
    yield executor


@pytest.fixture(scope="function")
def service_info(test_config, swagger, database_connection):
    yield ServiceInfo(test_config["static_service_info"], swagger, database_connection)


@pytest.fixture(scope="function")
def log_config():
    # There is a special logger "tests" for test-associated logging.
    with open(os.path.join("config", "log-config.yaml")) as ff:
        log_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield log_config


@pytest.fixture(scope="function")
def logger(log_config):
    dictConfig(log_config)
    yield logging.getLogger("test")


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("ga4gh/wes/swagger/workflow_execution_service_1.0.0.yaml", "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger
