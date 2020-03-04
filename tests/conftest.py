import pytest
from ga4gh.wes.app import create_app

test_config = {
    "server": {
        "host": '0.0.0.0',
        "port": 4080,
        "debug": False},
    "debug": True
}


app = create_app(test_config)

@pytest.fixture(scope='module')
def client():
    print("test client")
    with app.app.test_client() as c:
        yield c

