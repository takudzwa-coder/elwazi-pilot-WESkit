import os
import pytest
import yaml
import requests
import time

from weskit.classes.ServiceInfo import ServiceInfo
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.core.container import DockerContainer
from weskit import create_app, Manager, WorkflowEngineFactory
from weskit import create_database


def get_redis_url(redis_container):
    url = "redis://{}:{}".format(
        redis_container.get_container_host_ip(),
        redis_container.get_exposed_port(6379)
    )
    print("REDISURL:%s"%redis_container.get_container_host_ip())
    return url



        
"""
KeyCloak Containers

"""



def getContainerProperties(container,port):
    return(
        {
        "ExternalHostname":container.get_container_host_ip(),
        "InternalPorts":list(container.ports.keys()),
        "ExposedPorts":container.get_exposed_port(port),
        "InternalIP":container.get_docker_client().bridge_ip(container._container.id)
        }
    )

@pytest.fixture(scope="session")
def MySQL_keycloak_container ():
    preDB=MySqlContainer('mysql:latest',MYSQL_USER="keycloak",MYSQL_PASSWORD="secret_password",MYSQL_DATABASE="keycloak",MYSQL_ROOT_PASSWORD= "secret_root_password")
    
    configfile=os.path.abspath("config/keycloak_schema.sql")
    print(configfile)
    preDB.with_volume_mapping(configfile,"/docker-entrypoint-initdb.d/test.sql")
    with  preDB as mysql:
        print(yaml.dump(getContainerProperties(mysql,'3306')))
        yield mysql
        print("Killing keycloaks MySQL")


# @pytest.fixture(scope="session")
# def test_app(database_container, redis_container, keycloak_container):
#     os.environ["BROKER_URL"] = get_redis_url(redis_container)
#     os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
#
#     keycloakContainerProperties = getContainerProperties(keycloak_container, '8080')
#     os.environ["OIDC_ISSUER_URL"] = "http://%s:%s/auth/realms/WESkit" % (
#         keycloakContainerProperties["ExternalHostname"],
#         keycloakContainerProperties["ExposedPorts"],
#     )
#     os.environ["WESKIT_PUBLIC_HOST_PORT"] = "https://localhost:5000"  # Not used
#     os.environ["OIDC_CLIENT_SECRET"] = "a8086bcc-44f3-40f9-9e15-fd5c3c98ab24"
#     os.environ["OIDC_REALM"] = "WESkit"
#     os.environ["OIDC_CLIENTID"] = "WESkit"
#
#     # import here because env vars need to be set before
#     from weskit import create_app
#
#     os.environ["WESKIT_CONFIG"] = "tests/config.yaml"
#
#     app = create_app()
#
#     os.environ["testing_only_tokenendpoint"] = app.OIDC_Login.oidc_config["token_endpoint"]
#     app.testing = True
#     with app.test_client() as testing_client:
#         ctx = app.app_context()
#         ctx.push()
#         yield testing_client

@pytest.fixture(scope="session")
def test_client(celery_session_app,
                test_database,
                redis_container,
                keycloak_container):
    print("huhu")
    os.environ["BROKER_URL"] = get_redis_url(redis_container)
    os.environ["RESULT_BACKEND"] = get_redis_url(redis_container)
    os.environ["WESKIT_CONFIG"] = "tests/weskit.yaml"
    os.environ["WESKIT_WORKFLOWS"] = os.getcwd()

    keycloakContainerProperties = getContainerProperties(keycloak_container, '8080')
    os.environ["OIDC_ISSUER_URL"] = "http://%s:%s/auth/realms/WESkit" % (
        keycloakContainerProperties["ExternalHostname"],
        keycloakContainerProperties["ExposedPorts"],
    )
    # Define Variables that would be defined in the docker stack file
    os.environ["WESKIT_PUBLIC_HOST_PORT"] = "https://localhost:5000"  # Not used
    os.environ["OIDC_CLIENT_SECRET"] = "a8086bcc-44f3-40f9-9e15-fd5c3c98ab24"
    os.environ["OIDC_REALM"] = "WESkit"
    os.environ["OIDC_CLIENTID"] = "WESkit"

    app = create_app(celery=celery_session_app,
                     database=test_database)
    app.testing = True
    os.environ["testing_only_tokenendpoint"] = app.OIDC_Login.oidc_config["token_endpoint"]
    with app.test_client() as testing_client:
        with app.app_context():
            # This sets `current_app` for accessing the Flask app in the tests.
            yield testing_client



@pytest.fixture(scope="session")
def keycloak_container(MySQL_keycloak_container):
    mysqlIP=getContainerProperties(MySQL_keycloak_container, '3306')["InternalIP"]

    kc_container=DockerContainer("jboss/keycloak")
    kc_container.with_exposed_ports('8080')
    kc_container.with_env("DB_VENDOR","mysql")
    kc_container.with_env("DB_PORT",'3306')
    kc_container.with_env("DB_ADDR", mysqlIP)
    kc_container.with_env("DB_USER","keycloak")
    kc_container.with_env("DB_PASSWORD","secret_password")
    kc_container.start()
    time.sleep(5)
    kc_port=kc_container.get_exposed_port('8080')
    kc_host=kc_container.get_container_host_ip()
    print("Waiting for Keycloak Container")
    print(yaml.dump(getContainerProperties(kc_container,'8080')))
    retry=20
    waitingSeconds=5
    kc_running=False
    for i in range(retry):
        try:
            print("connect to keycloak try : %d"%(i+1))
            requests.get("http://"+kc_host+":"+kc_port)
            kc_running=True
            print("connection attempted try %d: Success"%(i+1))
            break
        except Exception:
            print("connection attemped try %d: Failed - Will retry in %d seconds"%(i+1,waitingSeconds))
            time.sleep(waitingSeconds)
    assert kc_running
    print("KC ready")
    yield kc_container
    print("Killing KeyCloak")
    
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
                   data_dir=test_dir)
