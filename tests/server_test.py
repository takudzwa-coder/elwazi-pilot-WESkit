import pytest
from ga4gh.wes.wesnake import create_app

test_config = {
    "wes_server":{
        "host": '0.0.0.0',
        "port": 4080,
        "debug": False
    },
    "debug": True
}

@pytest.fixture
def test_app(database_connection):
    app = create_app(test_config, database_connection)
    with app.app.test_client() as testing_client:
        ctx = app.app.app_context()
        ctx.push()
        yield testing_client

def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    assert response.status_code == 200
