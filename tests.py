import pytest
import manna

@pytest.fixture
def client():
    with manna.app.test_client() as client:
        with manna.app.app_context():
            yield client

def test_series_edit(client):
    """Start with a blank database."""
    rv = client.get("/series/Evangelism/edit")
    assert b'Evangelism' in rv.data
    #assert b'No entries here so far' in rv.data

