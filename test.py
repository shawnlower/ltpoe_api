#!/usr/bin/env python
# run w/ python -i test.py
from pprint import pprint

import rdflib
from rdflib import URIRef, Variable, Literal, Graph, ConjunctiveGraph
from rdflib.namespace import Namespace, NamespaceManager
from rdflib import RDF, RDFS, OWL

g=ConjunctiveGraph()

LTP=Namespace('http://shawnlower.net/o/')
namespace_manager = NamespaceManager(g)
namespace_manager.bind('ltp', LTP, override=False)

g.namespace_manager = namespace_manager

g.load('./tests/testdata/data.rdf')
print(len(g))

