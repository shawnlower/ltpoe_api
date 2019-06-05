import requests
import unittest
from unittest import mock

import flask

app = flask.Flask(__name__)

def test_types():
    path = '/api/v1/types/'
    with app.test_request_context(path):
        assert flask.request.path == path
