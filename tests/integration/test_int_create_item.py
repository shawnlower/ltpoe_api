from unittest.mock import patch
from pprint import pprint

import flask
import pytest

import ltpapi
from ltpapi.models import LtpItem


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


def test_invalid_item(client):
    path = '/api/v1/items'

    # Missing 'name'
    rv = client.post(path, json={'itemType': 'Thing'})
    assert rv.status_code == 400, (rv.status_code, rv.data)

    # Missing 'type'
    rv = client.post(path, json={'name': 'name'})
    assert rv.status_code == 400, (rv.status_code, rv.data)

