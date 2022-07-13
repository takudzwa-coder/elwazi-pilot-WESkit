#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
import os
import shutil
import time
from pathlib import Path
from tempfile import mkdtemp

import pytest
import requests
import yaml
from testcontainers.core.container import DockerContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.redis import RedisContainer

from weskit import create_app, create_database, Manager, WorkflowEngineFactory, PathContext
from weskit.utils import create_validator
from weskit.classes.ServiceInfo import ServiceInfo

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def temporary_dir():
    tmpdir = mkdtemp(prefix=__name__)
    yield tmpdir
    shutil.rmtree(tmpdir)


def get_redis_url(redis_container):
    url = "redis://{}:{}".format(
        redis_container.get_container_host_ip(),
        redis_container.get_exposed_port(6379)
    )
    return url


def get_container_properties(container, port):
    return (
        {
            "ExternalHostname": container.get_container_host_ip(),
            "InternalPorts": list(container.ports.keys()),
            "ExposedPorts": container.get_exposed_port(port),
            "InternalIP": container.get_docker_client().bridge_ip(container._container.id)
        }
    )


@pytest.fixture(scope="session")
def mysql_keycloak_container():
    container = MySqlContainer('mysql:latest',
                               MYSQL_USER="keycloak",
                               MYSQL_PASSWORD="secret_password",
                               MYSQL_DATABASE="keycloak",
                               MYSQL_ROOT_PASSWORD="secret_root_password"
                               )

    configfile = os.path.abspath("tests/keycloak/keycloak_schema.sql")

    container.with_volume_mapping(configfile, "/docker-entrypoint-initdb.d/test.sql")
    with container as mysql:
        yield mysql


def _setup_test_app(redis_container,
                    celery_session_app,
                    test_database,
                    config):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["CELERY_RESULT_BACKEND"] = get_redis_url(redis_container)
    os.environ["WESKIT_LOG_CONFIG"] = os.path.join("config", "devel-log-config.yaml")
    os.environ["WESKIT_CONFIG"] = config
    os.environ["WESKIT_DATA"] = "test-data/"
    os.environ["WESKIT_WORKFLOWS"] = os.getcwd()
    os.environ["WESKIT_S3_ENDPOINT"] = "http://localhost:9000"
    os.environ["WESKIT_S3_ID"] = "minioadmin"
    os.environ["WESKIT_S3_SECRET"] = "minioadmin"
    os.environ["WESKIT_S3_REGION"] = "us-east-1"

    app = create_app(celery=celery_session_app,
                     database=test_database)
    app.testing = True
    return app


@pytest.fixture(scope="session")
def login_app(redis_container,
              celery_session_app,
              test_database,
              keycloak_container):
    yield _setup_test_app(redis_container,
                          celery_session_app,
                          test_database,
                          config="tests/weskit.yaml")


@pytest.fixture(scope="session")
def nologin_app(redis_container,
                celery_session_app,
                test_database):
    yield _setup_test_app(redis_container,
                          celery_session_app,
                          test_database,
                          config="tests/weskit_nologin.yaml")


@pytest.fixture(scope="session")
def test_client(login_app):
    with login_app.test_client() as testing_client:
        with login_app.app_context():
            # This sets `current_app` and `current_user` for the tests.
            yield testing_client


@pytest.fixture(scope="session")
def test_client_nologin(nologin_app):
    with nologin_app.test_client() as testing_client:
        with nologin_app.app_context():
            # The app_context() sets `current_app` and `current_user` for the tests.
            yield testing_client


@pytest.fixture(scope="session")
def keycloak_container(mysql_keycloak_container):
    mysql_ip = get_container_properties(mysql_keycloak_container, '3306')["InternalIP"]
    kc_container = DockerContainer("jboss/keycloak")
    kc_container.with_exposed_ports('8080')
    # Keycloak admin UI login credentials are defined in tests/keycloak/keycloak_schema.sql.
    # as admin:admin. The following does not work here:
    # kc_container.with_env("KEYCLOAK_USER", "admins")
    # kc_container.with_env("KEYCLOAK_PASSWORD", "test")
    kc_container.with_env("DB_VENDOR", "mysql")
    kc_container.with_env("DB_PORT", '3306')
    kc_container.with_env("DB_ADDR", mysql_ip)
    kc_container.with_env("DB_USER", "keycloak")
    kc_container.with_env("DB_PASSWORD", "secret_password")

    with kc_container as keycloak:
        time.sleep(5)

        kc_port = keycloak.get_exposed_port('8080')
        kc_host = keycloak.get_container_host_ip()

        retry = 20
        waiting_seconds = 5
        kc_running = False
        for i in range(retry):
            try:
                requests.get("http://" + kc_host + ":" + kc_port)
                kc_running = True
                break
            except Exception:
                logger.warning("Retrying connecting to Keycloak container {}/{}".format(i, retry))
                time.sleep(waiting_seconds)

        assert kc_running

        # Define Variables that would be defined in the docker stack file
        os.environ["OIDC_ISSUER_URL"] = "http://%s:%s/auth/realms/WESkit" % (kc_host, kc_port)
        os.environ["OIDC_CLIENT_SECRET"] = "a8086bcc-44f3-40f9-9e15-fd5c3c98ab24"
        os.environ["OIDC_REALM"] = "WESkit"
        os.environ["OIDC_CLIENTID"] = "WESkit"

        yield keycloak


@pytest.fixture(scope="session")
def test_validation():
    default_validation_config = "config/validation.yaml"
    with open(default_validation_config, "r") as yaml_file:
        validation = yaml.load(yaml_file, Loader=yaml.FullLoader)
        logger.debug("Read validation specification from " +
                     default_validation_config)
    yield validation


@pytest.fixture(scope="session")
def test_config(test_validation):
    # This uses a dedicated test configuration YAML.
    with open("tests/weskit.yaml", "r") as ff:
        raw_config = yaml.load(ff, Loader=yaml.FullLoader)
    validation_result = create_validator(test_validation)(raw_config)
    assert isinstance(validation_result, dict)
    yield validation_result


@pytest.fixture(scope="session")
def database_container():
    MONGODB_CONTAINER = "mongo:5.0.6"

    db_container = MongoDbContainer(MONGODB_CONTAINER)

    with db_container as mongoDB:
        # Add delay to avoid empty container port, dependent on time docker needs to start container
        time.sleep(0.5)

        os.environ["WESKIT_DATABASE_URL"] = mongoDB.get_connection_url()

        yield mongoDB


@pytest.fixture(scope="session")
def test_database(database_container):
    database = create_database(database_container.get_connection_url())
    # We have to initialize the MongoClient.
    database.initialize()
    yield database
    database._runs.drop()


@pytest.fixture(scope="session")
def redis_container():
    redis_container = RedisContainer("redis:6.2.6-alpine")
    with redis_container as rc:
        os.environ["BROKER_URL"] = get_redis_url(rc)
        os.environ["CELERY_RESULT_BACKEND"] = get_redis_url(rc)
        yield rc


@pytest.fixture(scope="session")
def celery_config(redis_container):
    return {
        "broker_url": get_redis_url(redis_container),
        "result_backend": get_redis_url(redis_container),
        "task_track_started": True,
        "serializer": "WESkitJSON",
        "task_serializer": "WESkitJSON",
        "result_serializer": "WESkitJSON",
        "accept_content": ["application/x-WESkitJSON"]
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


def create_manager(celery_session_app, redis_container, test_config, test_database,
                   require_workdir_tag: bool):
    workflows_base_dir = Path(os.getcwd()).absolute()
    os.environ["WESKIT_WORKFLOWS"] = str(workflows_base_dir)
    test_dir = Path("test-data")
    if not (test_dir.exists() and test_dir.is_dir()):
        test_dir.mkdir()
    common_context = PathContext(workflows_dir=workflows_base_dir,
                                 data_dir=test_dir)
    return Manager(celery_app=celery_session_app,
                   database=test_database,
                   executor=test_config["executor"],
                   workflow_engines=WorkflowEngineFactory.
                   create(
                       test_config
                       ["static_service_info"]
                       ["default_workflow_engine_parameters"]),
                   weskit_context=common_context,
                   executor_context=common_context,
                   require_workdir_tag=require_workdir_tag)


@pytest.fixture(scope="session")
def manager(celery_session_app, redis_container, test_config, test_database):
    return create_manager(celery_session_app, redis_container, test_config, test_database, False)


@pytest.fixture(scope="session")
def manager_rundir(celery_session_app, redis_container, test_config, test_database):
    return create_manager(celery_session_app, redis_container, test_config, test_database, True)
