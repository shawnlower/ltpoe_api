from pprint import pprint
from unittest.mock import Mock, patch

import flask
import pytest

import ltpapi
from ltpapi.models import LtpItem


def test_invalid_path(client):
    path = 'foobizbar'
    rv = client.get(path)
    assert rv.status_code == 404


@patch("ltpapi.store.SparqlDatastore.create_item")
def test_valid_item(mock_create_item):
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
def test_create_item_on_db_failure(mock_create_item):
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


def test_invalid_item(client):
    path = '/api/v1/items'

    # Missing 'name'
    rv = client.post(path, json={'itemType': 'Thing'})
    assert rv.status_code == 400, (rv.status_code, rv.data)

    # Missing 'type'
    rv = client.post(path, json={'name': 'name'})
    assert rv.status_code == 400, (rv.status_code, rv.data)

