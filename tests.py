import pytest
import manna

@pytest.fixture
def client():
    with manna.app.test_client() as client:
        with manna.app.app_context():
            yield client

def test_root_index(client):
    """Start with a blank database."""
    rv = client.get("/")
    import pdb; pdb.set_trace()

