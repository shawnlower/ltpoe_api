import os
import tempfile
from tempfile import NamedTemporaryFile

import flask
from flask import current_app
import pytest
from rdflib.term import URIRef

from ltpapi import create_app
from ltpapi.models import LtpType
from ltpapi.store import get_connection


@pytest.fixture()
def app():
    """
    Setup our store with some fake data. Ensure that get_items
    returns what we expect.
    """
    db_fd, db_filename = tempfile.mkstemp()

    config = {
            'STORE_TYPE': 'sqlite',
            'STORE_FILE': db_filename,
            'STORE_CREATE': 'True',
            'STORE_PREFIX': 'http://shawnlower.net/o/'
    }
    app = create_app(config=config)

    yield app

    os.close(db_fd)
    print("teardown")


class TestSqlite():

    def test_load(self, app):
        """Ensure we can load data from a file (in RDF/OWL format)"""

        with app.app_context():
            conn = get_connection(current_app)
            n3 = conn.load('tests/testdata/root-ontology.owl')

            subj = URIRef('http://shawnlower.net/o/Task')
            assert subj in conn._graph.subjects()

    def test_dump(self, app):
        """Ensure serialized data is sane"""

        with app.app_context():
            conn = get_connection(current_app)
            data = 'ltp:Person a owl:Class ;'
            expected_len = 5766

            n3 = conn.load('tests/testdata/root-ontology.owl')
            n3 = conn.dump()

        assert data in n3
        assert len(n3) == expected_len

    def test_create_type_no_parent(self, app):
        """Ensure we can create a basic LtpType and then read it back"""

        with app.app_context():
            conn = get_connection(current_app)

            name = 'Book'
            desc = 'A physical or digital book'
            resp = conn.create_type(name, desc)

            assert type(resp) == LtpType
            assert str(resp.name) == name
            assert str(resp.description) == desc

    def test_create_type_with_parent(self, app):
        """Ensure we can create a basic LtpType and then read it back"""

        with app.app_context():
            conn = get_connection(current_app)

            name = 'Book'
            desc = 'A physical or digital book'
            resp = conn.create_type(name, desc)

            name = 'Ebook'
            parent = 'Book'
            desc = 'A digital book'
            resp = conn.create_type(name, desc, parent)

        assert type(resp) == LtpType
        assert str(resp.name) == name
        assert str(resp.description) == desc
