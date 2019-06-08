from pprint import pprint

import flask
import pytest

import ltpapi


def test_invalid_path(client):
    path = 'foobizbar'
    rv = client.get(path)
    assert rv.status_code == 404

def test_valid_type(client):
    path = '/api/v1/items'

    rv = client.post(path,
            data={'itemType': 'Thing', 'name': 'A test thing'})

    assert rv.status_code == 201

