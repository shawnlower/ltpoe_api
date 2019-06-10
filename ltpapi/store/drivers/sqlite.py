from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, URIRef

class SqliteDatasource():
    def __init__(self, config):
        self.config = config
        self.graph = ConjunctiveGraph('SPARQLStore',
                     identifier=config['prefix'])
        self.graph.open(config['endpoint'])


