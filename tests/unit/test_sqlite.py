import os
from tempfile import NamedTemporaryFile

import flask
import pytest
from rdflib.term import URIRef

from ltpapi import create_app
from ltpapi.models import LtpType
from ltpapi.store import get_connection

from . import sqlite_connection

class TestSqlite():

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

    def test_create_type_no_parent(self, sqlite_connection):
        """Ensure we can create a basic LtpType and then read it back"""
        conn = sqlite_connection
        name = 'Book'
        desc = 'A physical or digital book'
        resp = conn.create_type(name, desc)

        assert type(resp) == LtpType
        assert str(resp.name) == name
        assert str(resp.description) == desc

    def test_create_type_with_parent(self, sqlite_connection):
        """Ensure we can create a basic LtpType and then read it back"""
        conn = sqlite_connection
        name = 'Ebook'
        parent = 'Book'
        desc = 'A digital book'
        resp = conn.create_type(name, desc, parent)

        assert type(resp) == LtpType
        assert str(resp.name) == name
        assert str(resp.description) == desc
