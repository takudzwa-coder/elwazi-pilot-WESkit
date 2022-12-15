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
from pathlib import Path
from tempfile import mkdtemp

import pytest
import nest_asyncio
import requests
import time
import yaml
from testcontainers.core.container import DockerContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.redis import RedisContainer

from weskit.classes.executor.cluster.lsf.LsfExecutor import LsfExecutor
from weskit.classes.executor.cluster.slurm.SlurmExecutor import SlurmExecutor
from weskit import create_app, create_database, Manager, WorkflowEngineFactory, PathContext
from weskit.classes.RetryableSshConnection import RetryableSshConnection
from weskit.classes.ServiceInfo import ServiceInfo
from weskit.classes.executor.unix.LocalExecutor import LocalExecutor
from weskit.classes.executor.unix.SshExecutor import SshExecutor
from weskit.utils import create_validator, get_event_loop

logger = logging.getLogger(__name__)


def get_remote_config():
    with open("tests/remote.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def remote_config():
    return get_remote_config()


# Workaround against "RuntimeError" about already running loop.
# Compare: https://github.com/pytest-dev/pytest-asyncio/issues/112
# Note that fixtures that are used in the tests should still not be async, because they will
# be tried to be evaluated multiple times, which is not possible with coroutines (no referential
# transparency :( ).
nest_asyncio.apply()


@pytest.fixture(scope="session")
def event_loop():
    """
    See https://github.com/pexip/os-python-pytest-asyncio#event_loop

    Provide the global event loop via a fixture.
    """
    return get_event_loop()


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
                    config_file):
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["CELERY_RESULT_BACKEND"] = get_redis_url(redis_container)
    os.environ["WESKIT_LOG_CONFIG"] = os.path.join("config", "devel-log-config.yaml")
    os.environ["WESKIT_CONFIG"] = config_file
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
                          config_file="tests/weskit.yaml")


@pytest.fixture(scope="session")
def nologin_app(redis_container,
                celery_session_app,
                test_database):
    yield _setup_test_app(redis_container,
                          celery_session_app,
                          test_database,
                          config_file="tests/weskit_nologin.yaml")


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
    config_file = "tests/weskit.yaml"
    with open(config_file, "r") as ff:
        raw_config = yaml.load(ff, Loader=yaml.FullLoader)
    validation_result = create_validator(test_validation)(raw_config)
    assert isinstance(validation_result, dict)
    # Tests of the command task need this variable.
    os.environ["WESKIT_CONFIG"] = config_file
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
        test_config["workflow_engines"],
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
    workflows_base_dir = Path("tests")
    os.environ["WESKIT_WORKFLOWS"] = str(workflows_base_dir)
    test_dir = Path("test-data")
    if not (test_dir.exists() and test_dir.is_dir()):
        test_dir.mkdir()
    common_context = PathContext(workflows_dir=workflows_base_dir,
                                 data_dir=test_dir)
    return Manager(celery_app=celery_session_app,
                   database=test_database,
                   config=test_config,
                   workflow_engines=WorkflowEngineFactory.
                   create(test_config["workflow_engines"]),
                   weskit_context=common_context,
                   executor_context=common_context,
                   require_workdir_tag=require_workdir_tag)


@pytest.fixture(scope="session")
def manager(celery_session_app, redis_container, test_config, test_database):
    return create_manager(celery_session_app, redis_container, test_config, test_database, False)


@pytest.fixture(scope="session")
def manager_rundir(celery_session_app, redis_container, test_config, test_database):
    return create_manager(celery_session_app, redis_container, test_config, test_database, True)


def get_connection(event_loop, **kwargs):
    connection = RetryableSshConnection(**kwargs)
    event_loop.run_until_complete(connection.connect())
    return connection

# All the following fixtures could have been made async with pytest-async. However, that did
# not work well, because it gave RuntimeErrors about either existing event loops, or about
# multiple evaluations of co-routines. pytest-async seems not to be mature enough :P.


@pytest.fixture(scope="session")
def ssh_local_connection(remote_config, event_loop):
    return get_connection(event_loop, **(remote_config["ssh"]))


@pytest.fixture(scope="session")
def ssh_lsf_connection(remote_config, event_loop):
    return get_connection(event_loop, **(remote_config["lsf_submission_host"]["ssh"]))


@pytest.fixture(scope="session")
def ssh_slurm_connection(remote_config, event_loop):
    return get_connection(event_loop, **(remote_config["slurm_submission_host"]["ssh"]))


# The executor fixtures return pairs (tuples), of executor and the Path to the shared workdir to
# be used for tests. Where this does not apply (local and the SSH executor that is assumed to be
# logging in to localhost), instead of a Path, None is returned.

@pytest.fixture(scope="session")
def local_executor():
    return LocalExecutor(), None


@pytest.fixture(scope="session")
def ssh_executor(ssh_local_connection, event_loop):
    return SshExecutor(ssh_local_connection, event_loop), None


@pytest.fixture(scope="session")
def ssh_lsf_executor(ssh_lsf_connection, event_loop, remote_config):
    return LsfExecutor(SshExecutor(ssh_lsf_connection, event_loop)), \
        Path(remote_config["lsf_submission_host"]["shared_workdir"])


@pytest.fixture(scope="session")
def ssh_slurm_executor(ssh_slurm_connection, event_loop, remote_config):
    return SlurmExecutor(SshExecutor(ssh_slurm_connection, event_loop)), \
        Path(remote_config['slurm_submission_host']["shared_workdir"])


# Use these to parametrize your tests. Get the corresponding fixtures in the test body with
#
#   request.getfixturevalue(name + "_executor")
#
# request is another pytest-provided fixture that has to be the last parameter of the test
# function's signature.
executor_prefixes = [pytest.param("local")]

# The following ensures that only the executors are attempted to be used in the tests, that have
# a configuration in the remote.yaml. The pytest parameters allow the selection of groups of
# tests by the availability of the integration-test resources (e.g. a cluster).
_remote_config = get_remote_config()

if _remote_config is not None:
    if "ssh" in _remote_config:
        executor_prefixes.append(pytest.param("ssh", marks=[
            pytest.mark.ssh,
            pytest.mark.integration,
        ]))

    if "slurm_submission_host" in _remote_config:
        executor_prefixes.append(pytest.param("ssh_slurm", marks=[
            pytest.mark.ssh_slurm,
            pytest.mark.integration,
            pytest.mark.slow
        ]))

    if "lsf_submission_host" in _remote_config:
        executor_prefixes.append(pytest.param("ssh_lsf", marks=[
            pytest.mark.ssh_lsf,
            pytest.mark.integration,
            pytest.mark.slow
        ]))
