import pytest

import ltpapi

@pytest.fixture
def client(mocker):
    mocker.patch("ltpapi.db.SparqlDatasource.create_item", return_value=False)
    app = ltpapi.create_app()
    client = app.test_client()

    with app.app_context():
        pass

    yield client


@pytest.fixture
def app(mocker):
    mocker.patch("ltpapi.db.SparqlDatasource")
    app = ltpapi.create_app()
    return app
