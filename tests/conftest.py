import logging
import os
import pytest
import yaml
from wesnake.classes.Database import Database
from wesnake.classes.ServiceInfo import ServiceInfo
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from logging.config import dictConfig
from wesnake.classes.RunStatus import RunStatus


def get_redis_url(redis_container):
    url = "redis://{}:{}".format(
        redis_container.get_container_host_ip(),
        redis_container.get_exposed_port(6379)
    )
    return url


@pytest.fixture(scope="function")
def test_app(database_container, redis_container):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)

    # import here because env vars need to be set before
    from wesnake import create_app

    os.environ["WESNAKE_CONFIG"] = "tests/config.yaml"

    app = create_app()

    app.testing = True
    with app.test_client() as testing_client:
        ctx = app.app_context()
        ctx.push()
        yield testing_client


@pytest.fixture(scope="function")
def test_config():
    # This uses a dedicated test configuration YAML.
    with open("tests/config.yaml", "r") as ff:
        test_config = yaml.load(ff, Loader=yaml.FullLoader)
    yield test_config


@pytest.fixture(scope="function")
def database_container():

    MONGODB_CONTAINER = "mongo:4.2.3"

    db_container = MongoDbContainer(MONGODB_CONTAINER)
    db_container.start()
    os.environ["WESNAKE_DATABASE_URL"] = db_container.get_connection_url()

    yield db_container

@pytest.fixture(scope="function")
def database_connection(database_container):
    from wesnake import create_database

    database = create_database()

    yield database
    database._db_runs().drop()

@pytest.fixture(scope="session")
def redis_container():
    print("redis_container")
    redis_container = RedisContainer("redis:6.0.1-alpine")
    redis_container.start()
    return redis_container


@pytest.fixture(scope="session")
def celery_config(redis_container):
    print("celery_config")
    return {
        "broker_url": get_redis_url(redis_container),
        "result_backend": get_redis_url(redis_container)
    }


@pytest.fixture(scope="session")
def celery_worker_pool():
    return 'prefork'


@pytest.fixture(scope="function")
def service_info(test_config, swagger, database_connection):
    yield ServiceInfo(
        test_config["static_service_info"],
        swagger,
        database_connection
    )


@pytest.fixture(scope="function")
def swagger(database_connection):
    with open("wesnake/api/workflow_execution_service_1.0.0.yaml",
              "r") as ff:
        swagger = yaml.load(ff, Loader=yaml.FullLoader)
    yield swagger


@pytest.fixture(scope="function")
def snakemake(database_connection, redis_container, test_config):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    from wesnake.classes.Snakemake import Snakemake
    snakemake = Snakemake(config=test_config, datadir="tmp/")
    yield snakemake

import json, yaml, sys, time

def get_workflow_data(snakefile, config):
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "Snakemake",
        "workflow_type_version": "5.8.2",
        "workflow_url": snakefile
    }
    return data

@pytest.fixture(scope="function")
def snakemake_wf1_data():
    data = get_workflow_data(
        snakefile="tests/wf1/Snakefile",
        config="tests/wf1/config.yaml")
    yield data


@pytest.fixture(scope="function")
def snakemake_wf2_data():
    data = get_workflow_data(
        snakefile="tests/wf2/Snakefile",
        config="tests/wf2/config.yaml")
    yield data