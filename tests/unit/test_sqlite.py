import os
from tempfile import NamedTemporaryFile

import flask
import pytest
from rdflib.term import URIRef

from ltpapi import create_app
from ltpapi.models import LtpType
from ltpapi.store import get_connection

@pytest.fixture(scope="module")
def sqlite_connection():
    app = create_app()
    db = NamedTemporaryFile()

    app.config['STORE_TYPE'] = 'sqlite'
    app.config['STORE_FILE'] = db.name
    yield get_connection(app)
    db.close()

class TestItem():

    def test_load(self, sqlite_connection):
        """Ensure we can load data from a file (in RDF/OWL format)"""
        conn = sqlite_connection
        n3 = conn.load('tests/testdata/root-ontology.owl')

        subj = URIRef('http://shawnlower.net/o/Task')
        assert subj in conn._graph.subjects()

    def test_dump(self, sqlite_connection):
        """Ensure serialized data is sane"""

        conn = sqlite_connection
        data = 'ltp:Person a owl:Class ;'
        expected_len = 5766

        n3 = conn.load('tests/testdata/root-ontology.owl')
        n3 = conn.dump().decode('utf-8')

        assert data in n3
        assert len(n3) == expected_len

    def test_create_type(self, sqlite_connection):
        """Ensure we can create a basic LtpType and then read it back"""
        conn = sqlite_connection
        t = LtpType('test name', 'this is a test description')

        conn.create_type(t)




