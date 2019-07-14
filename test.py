#!/usr/bin/env python
# run w/ python -i test.py
import argparse
from pprint import pprint
import sys

import rdflib
from rdflib import URIRef, Variable, Literal, Graph, ConjunctiveGraph
from rdflib.namespace import Namespace, NamespaceManager
from rdflib import RDF, RDFS, OWL

ns = 'http://shawnlower.net/o/'
LTP = Namespace(ns)

parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='?', default='')
args = parser.parse_args()

if args.file:
    g = ConjunctiveGraph('SQLite', identifier=ns)
    g.open(args.file)
else:
    g = ConjunctiveGraph()

namespace_manager = NamespaceManager(g)
namespace_manager.bind('ltp', LTP, override=False)
g.namespace_manager = namespace_manager

if len(list(g)) == 0:
    datafile='./tests/testdata/data.rdf'
    print(f"Loading from {datafile}")
    g.load(datafile)

print(len(g))

