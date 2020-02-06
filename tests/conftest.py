import pytest

from app import create_app


test_config = {
    "server":{
        "host": '0.0.0.0',
        "port": 8080,
        "debug": False
    }
}
    
app = create_app(test_config)

@pytest.fixture(scope='module')
def client():
    print("test client")
    with app.app.test_client() as c:
        yield c

