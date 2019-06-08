from unittest.mock import Mock, patch

import flask
import pytest

import ltpapi
from ltpapi.models import LtpItem

def test_get_items(app):
    # app.config['endpoint'] = ''
    path = '/api/v1/items/'
    with app.test_client() as c:
        resp = c.get(path, follow_redirects=True)
        assert False, (resp, resp.json)

