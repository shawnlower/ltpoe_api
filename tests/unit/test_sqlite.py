import flask
import pytest

from ltpapi import create_app
from ltpapi.store import get_connection

@pytest.fixture
def sqlite_connection():
    app = create_app()
    app.config['STORE_TYPE'] = 'SqliteDatastore'
    return get_connection(app)

class TestItem():

    def test_dump(self, sqlite_connection):
        conn = sqlite_connection
        n3 = conn.dump()

        assert len(n3) > 0

