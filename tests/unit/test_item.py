import json
from pprint import pprint
import os
import tempfile
from unittest.mock import Mock, patch

import flask
import pytest

import ltpapi
from ltpapi.models import LtpItem
from ltpapi.store import get_connection
from ltpapi.store.drivers import SqliteDatastore


@pytest.fixture()
def client():
    """
    Setup our store with some fake data. Ensure that get_items
    returns what we expect.
    """
    app = ltpapi.create_app()
    db_fd, db_filename = tempfile.mkstemp()

    cfg = { k: v for k,v in app.config.items() if not
            k.lower().startswith('store') }
    cfg.update({
            'STORE_TYPE': 'sqlite',
            'STORE_FILE': db_filename,
            'STORE_CREATE': 'True',
            'STORE_PREFIX': 'http://shawnlower.net/o/'
    })

    app.config = cfg
    client = app.test_client()
    with app.app_context():
        conn = get_connection(app)
        #conn.load('tests/testdata/root-ontology.owl')
        conn.load('tests/testdata/data.rdf')
    app.config['STORE_CREATE'] = 'false'

    print("setup: {} triples loaded.".format(len(conn._graph)))
    yield client
    os.close(db_fd)
    print("teardown")

class TestItem():
    def setUp(self):
        pass

    def test_invalid_path(self, client):
        path = 'foobizbar'
        rv = client.get(path)
        assert rv.status_code == 404

    def test_get_items(self, client):

        path = '/api/v1/items/'
        rv = client.get(path)


        print('got', rv)
        assert rv.status_code == 200, (rv, rv.data)
        resp = json.loads(rv.data)
        pprint(resp['data'])
        assert len(resp['data']) == 8



    @patch("ltpapi.store.SparqlDatastore.create_item")
    def test_valid_item(self, mock_create_item):
        """
        Assuming that our connection returns a valid LtpItem
        the API should accept and return that item
        """

        name='A test thing'
        itemType='Thing'

        item = LtpItem(name=name, itemType=itemType, id=0)
        mock_create_item.return_value = item

        app = ltpapi.create_app()
        with app.test_client() as c:
            path = '/api/v1/items'
            rv = c.post(path,
                    json={'name': name, 'itemType': itemType})

            assert 'item' in rv.json
            response_item = rv.json['item'] 

            assert ('name', name) in response_item.items() and \
                   ('itemType', itemType) in response_item.items()


    @patch("ltpapi.store.SparqlDatastore.create_item")
    def test_create_item_on_db_failure(self, mock_create_item):
        """
        We should get a generic error back on DB failures
        """

        mock_create_item.side_effect = Exception('Boom')

        app = ltpapi.create_app()
        with app.test_client() as c:
            path = '/api/v1/items'
            rv = c.post(path,
                   json={'itemType': 'Thing', 'name': 'A test thing'})
            assert rv.status_code == 500, (rv, rv.data)


    def test_invalid_item(self, client):
        path = '/api/v1/items'

        # Missing 'name'
        rv = client.post(path, json={'itemType': 'Thing'})
        assert rv.status_code == 400, (rv.status_code, rv.data)

        # Missing 'type'
        rv = client.post(path, json={'name': 'name'})
        assert rv.status_code == 400, (rv.status_code, rv.data)

