import pytest

import ltpapi

@pytest.fixture
def client():
    app = ltpapi.create_app()
    client = app.test_client()

    with app.app_context():
        pass

    yield client


