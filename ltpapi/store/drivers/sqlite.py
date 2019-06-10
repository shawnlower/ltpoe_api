from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, URIRef

class SqliteDatastore():
    def __init__(self, config):
        self.config = config
        self.graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])
        self.graph.open(config['endpoint'])

    def dump(format='n3') -> str:
        """
        Dump the data from the store
        """
        return self.graph.serialize(format='n3')

